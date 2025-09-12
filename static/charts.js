// // static/chart.js
// document.addEventListener('DOMContentLoaded', function() {
//     // Check if we're on the profit analysis page
//     try {

//         if (document.getElementById('profitChart')) {
//             initializeProfitChart();
//         }
// }       catch (error) {
//             console.error("Chart initialization failed:", error);
//     // Display error to user
//         const container = document.querySelector('.chart-wrapper');
//         if (container) {
//             container.innerHTML = `
//                 <div class="chart-error">
//                     <i class="fas fa-exclamation-triangle"></i>
//                     <p>Failed to load profit chart</p>
//                     <p>${error.message}</p>
//                 </div>
//         `   ;
//     }
// }
// });



// function initializeProfitChart() {
//     // Get the chart data from the HTML element
//     const chartDataElement = document.getElementById('chart-data');
//     if (!chartDataElement) {
//         console.error("Chart data element not found");
//         return;
//     }

//     try {
//         const chartData = JSON.parse(chartDataElement.dataset.chart);
//         console.log("Parsed chart data:", chartData);
        
//         const ctx = document.getElementById('profitChart').getContext('2d');
        
//         // Create the chart with enhanced options
//         new Chart(ctx, {
//             type: 'line',
//             data: {
//                 labels: chartData.dates,
//                 datasets: [
//                     {
//                         label: 'Profit',
//                         data: chartData.profits,
//                         borderColor: 'rgb(54, 162, 235)',
//                         backgroundColor: 'rgba(54, 162, 235, 0.1)',
//                         borderWidth: 3,
//                         fill: true,
//                         tension: 0.3,
//                         pointRadius: 4,
//                         pointHoverRadius: 6
//                     },
//                     {
//                         label: 'Sales',
//                         data: chartData.sales,
//                         borderColor: 'rgb(75, 192, 192)',
//                         backgroundColor: 'rgba(75, 192, 192, 0.1)',
//                         borderWidth: 3,
//                         fill: true,
//                         tension: 0.3,
//                         pointRadius: 4,
//                         pointHoverRadius: 6
//                     },
//                     {
//                         label: 'Expenses',
//                         data: chartData.expenses,
//                         borderColor: 'rgb(255, 99, 132)',
//                         backgroundColor: 'rgba(255, 99, 132, 0.1)',
//                         borderWidth: 3,
//                         fill: true,
//                         tension: 0.3,
//                         pointRadius: 4,
//                         pointHoverRadius: 6
//                     }
//                 ]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 plugins: {
//                     legend: {
//                         position: 'top',
//                         labels: {
//                             font: {
//                                 size: 14,
//                                 family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
//                             },
//                             padding: 20,
//                             usePointStyle: true,
//                             pointStyle: 'circle'
//                         }
//                     },
//                     tooltip: {
//                         backgroundColor: 'rgba(0, 0, 0, 0.8)',
//                         titleFont: {
//                             size: 16
//                         },
//                         bodyFont: {
//                             size: 14
//                         },
//                         padding: 12,
//                         displayColors: true,
//                         callbacks: {
//                             label: function(context) {
//                                 return context.dataset.label + ': KES ' + context.parsed.y.toLocaleString();
//                             }
//                         }
//                     }
//                 },
//                 scales: {
//                     y: {
//                         beginAtZero: true,
//                         grid: {
//                             color: 'rgba(0, 0, 0, 0.05)'
//                         },
//                         ticks: {
//                             callback: function(value) {
//                                 return 'KES ' + value.toLocaleString();
//                             },
//                             font: {
//                                 size: 12
//                             }
//                         },
//                         title: {
//                             display: true,
//                             text: 'Amount (KES)',
//                             font: {
//                                 size: 14,
//                                 weight: 'bold'
//                             }
//                         }
//                     },
//                     x: {
//                         grid: {
//                             display: false
//                         },
//                         ticks: {
//                             font: {
//                                 size: 12
//                             }
//                         }
//                     }
//                 },
//                 interaction: {
//                     mode: 'index',
//                     intersect: false
//                 },
//                 hover: {
//                     mode: 'index',
//                     intersect: false
//                 }
//             }
//         });
//     } catch (error) {
//         console.error("Error initializing chart:", error);
//     }
// }