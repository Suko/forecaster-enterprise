/**
 * Chart.js plugin registration
 * Client-side only plugin to register Chart.js and plugins
 */

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from "chart.js";
import zoomPlugin from "chartjs-plugin-zoom";
import annotationPlugin from "chartjs-plugin-annotation";

export default defineNuxtPlugin(() => {
  // Register Chart.js components
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    zoomPlugin,
    annotationPlugin
  );
});
