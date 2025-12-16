/**
 * Demo API Composable
 * Provides mock API responses using static JSON data files
 * Used for self-hosted static demo deployments
 */

import type { DashboardResponse } from "~/types/dashboard";
import type { Product, ProductListResponse } from "~/types/product";
import type { Recommendation } from "~/types/recommendation";
import type { CartResponse, PurchaseOrder, PurchaseOrdersListResponse } from "~/types/order";
import type { Supplier, SupplierListResponse } from "~/types/supplier";

// Cache for loaded data
const dataCache: Record<string, any> = {};

/**
 * Load JSON data from public/demo-data directory
 */
async function loadDemoData<T>(filename: string): Promise<T> {
  if (dataCache[filename]) {
    return dataCache[filename] as T;
  }
  
  try {
    const data = await $fetch<T>(`/demo-data/${filename}`);
    dataCache[filename] = data;
    return data;
  } catch (error) {
    console.error(`Failed to load demo data: ${filename}`, error);
    throw error;
  }
}

/**
 * Simulate network delay for realistic demo experience
 */
function simulateDelay(ms: number = 200): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export const useDemoApi = () => {
  /**
   * Get dashboard data
   */
  const getDashboard = async (): Promise<DashboardResponse> => {
    await simulateDelay(300);
    return await loadDemoData<DashboardResponse>("dashboard.json");
  };

  /**
   * Get products list with filtering and pagination
   */
  const getProducts = async (params?: {
    search?: string;
    category?: string;
    status?: string;
    supplier_id?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_order?: "asc" | "desc";
  }): Promise<ProductListResponse> => {
    await simulateDelay(250);
    
    let products = await loadDemoData<Product[]>("products.json");
    
    // Apply filters
    if (params?.search) {
      const searchLower = params.search.toLowerCase();
      products = products.filter(p => 
        p.item_id.toLowerCase().includes(searchLower) ||
        p.product_name?.toLowerCase().includes(searchLower) ||
        p.category?.toLowerCase().includes(searchLower)
      );
    }
    
    if (params?.category) {
      products = products.filter(p => p.category === params.category);
    }
    
    if (params?.status) {
      products = products.filter(p => p.status === params.status);
    }
    
    if (params?.supplier_id) {
      products = products.filter(p => 
        p.suppliers?.some(s => s.supplier_id === params.supplier_id)
      );
    }
    
    // Apply sorting
    if (params?.sort_by) {
      const sortKey = params.sort_by as keyof Product;
      const order = params.sort_order || "asc";
      
      products.sort((a, b) => {
        let aVal: any = a[sortKey];
        let bVal: any = b[sortKey];
        
        // Handle numeric values
        if (sortKey === "dir" || sortKey === "stockout_risk" || sortKey === "current_stock") {
          aVal = Number(aVal);
          bVal = Number(bVal);
        } else if (sortKey === "inventory_value" || sortKey === "unit_cost") {
          aVal = parseFloat(String(aVal));
          bVal = parseFloat(String(bVal));
        }
        
        if (order === "asc") {
          return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        } else {
          return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        }
      });
    }
    
    // Apply pagination
    const page = params?.page || 1;
    const pageSize = params?.page_size || 50;
    const total = products.length;
    const totalPages = Math.ceil(total / pageSize);
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedProducts = products.slice(startIndex, endIndex);
    
    return {
      items: paginatedProducts,
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    };
  };

  /**
   * Get single product by item_id
   */
  const getProduct = async (itemId: string): Promise<Product> => {
    await simulateDelay(200);
    
    const products = await loadDemoData<Product[]>("products.json");
    const product = products.find(p => p.item_id === itemId);
    
    if (!product) {
      throw createError({
        statusCode: 404,
        statusMessage: `Product not found: ${itemId}`,
      });
    }
    
    return product;
  };

  /**
   * Get recommendations
   */
  const getRecommendations = async (params?: {
    recommendation_type?: string;
    priority?: string;
  }): Promise<any[]> => {
    await simulateDelay(250);
    
    let recommendations = await loadDemoData<Recommendation[]>("recommendations.json");
    
    // Load products to get DIR and stockout risk for urgencyDetails
    const products = await loadDemoData<Product[]>("products.json");
    
    // Transform recommendations to include urgencyDetails (DemoRecommendation format)
    const enhancedRecommendations = recommendations.map(rec => {
      const product = products.find(p => p.item_id === rec.item_id);
      
      // Calculate risk score from stockout_risk if available
      const riskScore = product?.stockout_risk 
        ? Math.round(product.stockout_risk * 100) 
        : rec.type === 'URGENT' ? 85 : rec.type === 'REORDER' ? 65 : 30;
      
      // Get DIR from product or estimate based on type
      const dir = product?.dir || (rec.type === 'URGENT' ? 5 : rec.type === 'REORDER' ? 10 : 50);
      
      // Get lead time from product supplier or default
      const leadTime = product?.suppliers?.[0]?.lead_time_days || 7;
      
      // Format velocity string
      const velocity = product?.sales_velocity ? 
        `${product.sales_velocity.avg_7d.toFixed(1)}/7d, ${product.sales_velocity.avg_30d.toFixed(1)}/30d` : 
        'N/A';
      
      return {
        ...rec,
        urgencyDetails: {
          dir: dir,
          leadTime: leadTime,
          velocity: velocity,
          riskScore: riskScore,
        },
      };
    });
    
    // Apply filters
    if (params?.recommendation_type) {
      return enhancedRecommendations.filter(r => r.type === params.recommendation_type);
    }
    
    if (params?.priority) {
      return enhancedRecommendations.filter(r => r.priority === params.priority);
    }
    
    return enhancedRecommendations;
  };

  /**
   * Get cart
   */
  const getCart = async (): Promise<CartResponse> => {
    await simulateDelay(150);
    
    // Try to load from localStorage first (for demo persistence)
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('demo-cart');
      if (stored) {
        try {
          const cart = JSON.parse(stored);
          // Only use localStorage cart if it has items
          if (cart && cart.items && Array.isArray(cart.items) && cart.items.length > 0) {
            return cart;
          }
          // If localStorage cart is empty, clear it and load from file
          localStorage.removeItem('demo-cart');
        } catch (e) {
          // Invalid JSON, clear it and continue to load from file
          if (typeof window !== 'undefined') {
            localStorage.removeItem('demo-cart');
          }
        }
      }
    }
    
    // Load from file
    let cart = await loadDemoData<CartResponse>("cart.json");
    
    // Ensure cart has required structure
    if (!cart.items) {
      cart.items = [];
    }
    if (!cart.total_items) {
      cart.total_items = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    }
    if (!cart.total_value) {
      cart.total_value = cart.items.reduce(
        (sum, item) => sum + parseFloat(String(item.total_price || item.total_cost || 0)),
        0
      ).toFixed(2);
    }
    
    // Save to localStorage for persistence (even if empty, so we know we've loaded it)
    if (typeof window !== 'undefined') {
      localStorage.setItem('demo-cart', JSON.stringify(cart));
    }
    
    return cart;
  };

  /**
   * Add item to cart (demo - uses localStorage)
   */
  const addToCart = async (itemId: string, quantity: number, supplierId?: string): Promise<CartResponse> => {
    await simulateDelay(300);
    
    const cart = await getCart();
    const products = await loadDemoData<Product[]>("products.json");
    const product = products.find(p => p.item_id === itemId);
    
    if (!product) {
      throw createError({
        statusCode: 404,
        statusMessage: `Product not found: ${itemId}`,
      });
    }
    
    // Get supplier info
    const primarySupplier = product.suppliers?.[0];
    const supplier = supplierId 
      ? product.suppliers?.find(s => s.supplier_id === supplierId) || primarySupplier
      : primarySupplier;
    
    if (!supplier) {
      throw createError({
        statusCode: 400,
        statusMessage: `No supplier found for product: ${itemId}`,
      });
    }
    
    // Check if item already in cart (same item_id and supplier_id)
    const existingItem = cart.items?.find(
      item => item.item_id === itemId && item.supplier_id === supplier.supplier_id
    );
    
    if (existingItem) {
      existingItem.quantity += quantity;
      existingItem.total_price = (parseFloat(String(existingItem.unit_cost)) * existingItem.quantity).toFixed(2);
      existingItem.updated_at = new Date().toISOString();
    } else {
      cart.items = cart.items || [];
      const unitCost = parseFloat(product.unit_cost);
      cart.items.push({
        id: `cart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        session_id: 'demo-session',
        item_id: itemId,
        supplier_id: supplier.supplier_id,
        quantity,
        unit_cost: unitCost.toFixed(2),
        total_price: (unitCost * quantity).toFixed(2),
        packaging_unit: null,
        packaging_qty: null,
        notes: null,
        product_name: product.product_name || `Product ${itemId}`,
        supplier_name: supplier.supplier_name || 'Unknown Supplier',
        moq: supplier.moq || 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as any);
    }
    
    // Update totals
    cart.total_items = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    cart.total_value = cart.items.reduce(
      (sum, item) => sum + parseFloat(String(item.total_price || item.total_cost || 0)),
      0
    ).toFixed(2);
    
    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('demo-cart', JSON.stringify(cart));
      // Dispatch event for cart badge update
      window.dispatchEvent(new CustomEvent('cart-updated'));
    }
    
    return cart;
  };

  /**
   * Remove item from cart (demo - uses localStorage)
   */
  const removeFromCart = async (itemId: string, supplierId?: string): Promise<CartResponse> => {
    await simulateDelay(200);
    
    const cart = await getCart();
    
    // Filter out the item (match by item_id, and supplier_id if provided)
    if (supplierId) {
      cart.items = cart.items?.filter(
        item => !(item.item_id === itemId && item.supplier_id === supplierId)
      ) || [];
    } else {
      cart.items = cart.items?.filter(item => item.item_id !== itemId) || [];
    }
    
    // Update totals
    cart.total_items = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    cart.total_value = cart.items.reduce(
      (sum, item) => sum + parseFloat(String(item.total_price || item.total_cost || 0)),
      0
    ).toFixed(2);
    
    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('demo-cart', JSON.stringify(cart));
      // Dispatch event for cart badge update
      window.dispatchEvent(new CustomEvent('cart-updated'));
    }
    
    return cart;
  };

  /**
   * Get forecast data for a product
   */
  const getForecast = async (itemId: string): Promise<{
    historical: Array<{ date: string; value: number }>;
    forecast: Array<{ date: string; value: number; lower?: number; upper?: number }>;
    estimated_stockout_date?: string;
    recommended_reorder_window?: { start: string; end: string };
  }> => {
    await simulateDelay(250);
    
    const forecasts = await loadDemoData<Record<string, any>>("forecasts.json");
    const forecast = forecasts[itemId];
    
    if (!forecast) {
      // Generate basic forecast if not found
      const product = await getProduct(itemId);
      const today = new Date();
      const historical: Array<{ date: string; value: number }> = [];
      const forecastData: Array<{ date: string; value: number; lower: number; upper: number }> = [];
      
      // Generate 90 days of historical data
      for (let i = 90; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        historical.push({
          date: date.toISOString().split('T')[0],
          value: Math.floor(Math.random() * 20 + 10),
        });
      }
      
      // Generate 30 days of forecast
      for (let i = 1; i <= 30; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        const baseValue = 15;
        const value = baseValue + Math.random() * 5;
        forecastData.push({
          date: date.toISOString().split('T')[0],
          value: Math.floor(value),
          lower: Math.floor(value * 0.7),
          upper: Math.floor(value * 1.3),
        });
      }
      
      // Calculate stockout date based on DIR
      const stockoutDate = new Date(today);
      stockoutDate.setDate(stockoutDate.getDate() + Math.floor(product.dir));
      
      return {
        historical,
        forecast: forecastData,
        estimated_stockout_date: stockoutDate.toISOString().split('T')[0],
        recommended_reorder_window: {
          start: new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          end: new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        },
      };
    }
    
    return forecast;
  };

  /**
   * Get trend data
   */
  const getTrends = async (): Promise<{
    inventory_value: Array<{ date: string; value: number }>;
    sales_velocity: Array<{ date: string; value: number }>;
  }> => {
    await simulateDelay(200);
    return await loadDemoData("trends.json");
  };

  /**
   * Get suppliers
   */
  const getSuppliers = async (params?: {
    search?: string;
    supplier_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<SupplierListResponse> => {
    await simulateDelay(250);
    
    let suppliers = await loadDemoData<Supplier[]>("suppliers.json");
    
    // Apply filters
    if (params?.search) {
      const searchLower = params.search.toLowerCase();
      suppliers = suppliers.filter(s => 
        s.name.toLowerCase().includes(searchLower) ||
        s.id.toLowerCase().includes(searchLower)
      );
    }
    
    if (params?.supplier_type) {
      suppliers = suppliers.filter(s => s.supplier_type === params.supplier_type);
    }
    
    // Apply pagination
    const page = params?.page || 1;
    const pageSize = params?.page_size || 50;
    const total = suppliers.length;
    const totalPages = Math.ceil(total / pageSize);
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedSuppliers = suppliers.slice(startIndex, endIndex);
    
    return {
      items: paginatedSuppliers,
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    };
  };

  /**
   * Get single supplier by id
   */
  const getSupplier = async (id: string): Promise<Supplier> => {
    await simulateDelay(200);
    
    const suppliers = await loadDemoData<Supplier[]>("suppliers.json");
    const supplier = suppliers.find(s => s.id === id);
    
    if (!supplier) {
      throw createError({
        statusCode: 404,
        statusMessage: `Supplier not found: ${id}`,
      });
    }
    
    return supplier;
  };

  /**
   * Get purchase orders
   */
  const getPurchaseOrders = async (params?: {
    status?: string;
    supplier_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PurchaseOrdersListResponse> => {
    await simulateDelay(250);
    
    let orders = await loadDemoData<any[]>("purchase-orders.json");
    
    // Apply filters
    if (params?.status) {
      orders = orders.filter(o => o.status === params.status);
    }
    
    if (params?.supplier_id) {
      orders = orders.filter(o => o.supplier_id === params.supplier_id);
    }
    
    // Apply pagination
    const page = params?.page || 1;
    const pageSize = params?.page_size || 50;
    const total = orders.length;
    const totalPages = Math.ceil(total / pageSize);
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedOrders = orders.slice(startIndex, endIndex);
    
    return {
      items: paginatedOrders,
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    };
  };

  /**
   * Get single purchase order by id
   */
  const getPurchaseOrder = async (id: string): Promise<PurchaseOrder> => {
    await simulateDelay(200);
    
    const orders = await loadDemoData<PurchaseOrder[]>("purchase-orders-detail.json");
    const order = orders.find(o => o.id === id);
    
    if (!order) {
      throw createError({
        statusCode: 404,
        statusMessage: `Purchase order not found: ${id}`,
      });
    }
    
    return order;
  };

  /**
   * Create purchase order from cart (demo)
   */
  const createPurchaseOrderFromCart = async (data: {
    supplier_id: string;
    shipping_method?: string;
    shipping_unit?: string;
    notes?: string;
  }): Promise<PurchaseOrder> => {
    await simulateDelay(500);
    
    const cart = await getCart();
    const supplier = await getSupplier(data.supplier_id);
    
    // Get items for this supplier
    const supplierItems = cart.items?.filter(item => item.supplier_id === data.supplier_id) || [];
    
    if (supplierItems.length === 0) {
      throw createError({
        statusCode: 400,
        statusMessage: `No items in cart for supplier: ${data.supplier_id}`,
      });
    }
    
    // Generate a PO number
    const poNumber = `PO-${Date.now()}-${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
    
    // Calculate totals
    const totalValue = supplierItems.reduce(
      (sum, item) => sum + parseFloat(String(item.total_price || item.total_cost || 0)),
      0
    );
    
    // Create PO object
    const newPO: PurchaseOrder = {
      id: `po_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      po_number: poNumber,
      supplier_id: data.supplier_id,
      supplier_name: supplier.name,
      status: 'pending',
      total_value: totalValue.toFixed(2),
      shipping_method: data.shipping_method || null,
      shipping_unit: data.shipping_unit || null,
      notes: data.notes || null,
      items: supplierItems.map(item => ({
        id: `poi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        item_id: item.item_id,
        product_name: item.product_name,
        quantity: item.quantity,
        unit_cost: item.unit_cost,
        total_cost: item.total_price || item.total_cost,
        packaging_unit: item.packaging_unit || null,
        packaging_qty: item.packaging_qty || null,
        notes: item.notes || null,
      })),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      expected_delivery_date: null,
      received_at: null,
    } as any;
    
    // Remove items from cart
    cart.items = cart.items?.filter(item => item.supplier_id !== data.supplier_id) || [];
    cart.total_items = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    cart.total_value = cart.items.reduce(
      (sum, item) => sum + parseFloat(String(item.total_price || item.total_cost || 0)),
      0
    ).toFixed(2);
    
    // Save updated cart
    if (typeof window !== 'undefined') {
      localStorage.setItem('demo-cart', JSON.stringify(cart));
      window.dispatchEvent(new CustomEvent('cart-updated'));
    }
    
    return newPO;
  };

  return {
    getDashboard,
    getProducts,
    getProduct,
    getRecommendations,
    getCart,
    addToCart,
    removeFromCart,
    getForecast,
    getTrends,
    getSuppliers,
    getSupplier,
    getPurchaseOrders,
    getPurchaseOrder,
    createPurchaseOrderFromCart,
  };
};

