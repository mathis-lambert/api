const alltime = document.getElementById("alltime");

const AllTimeChart = new Chart(alltime, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "All Time",
        data: [],
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        borderColor: "rgba(255, 99, 132, 1)",
        borderWidth: 1,
      },
    ],
  },
  options: {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});
