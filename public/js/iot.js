const alltime = document.getElementById("alltime");

Chart.defaults.color = "white";

let allTimeData = [];
fetch("https://api.mathislambert.fr/iot/list").then((res) => {
  res.json().then((data) => {
    data.forEach((item) => {
      allTimeData.push(item);
    });
    displayChart(allTimeData);
  });
});
console.log(allTimeData);

function displayChart(data) {
  let temperature = data.map((item) => item.values.temperature);
  let humidity = data.map((item) => item.values.humidity);
  let pressure = data.map((item) => item.values.pressure);
  let labels = data.map((item) => item.timestamp);

  console.log(temperature);
  console.log(humidity);
  console.log(pressure);

  const config1 = {
    type: "line",
    data: {
      labels: labels.map((item) => new Date(item).toISOString().slice(11, 19)),
      datasets: [
        {
          label: "Temperature",
          tension: 0.5,

          data: temperature,
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgba(255, 99, 132, 1)",
        },
        {
          label: "Humidity",
          tension: 0.5,

          data: humidity,
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      elements: {
        point: {
          radius: 0,
        },
      },

      plugins: {
        legend: {
          position: "bottom",
        },
        title: {
          display: true,
          text: "Température et humidité",
          color: "white",
          font: {
            size: 20,
          },
        },
      },
    },
  };

  const config2 = {
    type: "line",
    data: {
      labels: labels.map((item) => new Date(item).toISOString().slice(11, 19)),
      datasets: [
        {
          label: "Pressure",
          tension: 0.5,

          data: pressure,
          backgroundColor: "rgba(255, 206, 86, 0.2)",
          borderColor: "rgba(255, 206, 86, 1)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      elements: {
        point: {
          radius: 0,
        },
      },

      plugins: {
        legend: {
          position: "bottom",
        },
        title: {
          display: true,
          text: "Pression atmosphérique",
          color: "white",
          font: {
            size: 20,
          },
        },
      },
    },
  };

  const ctx1 = document.getElementById("alltime1").getContext("2d");
  const myChart1 = new Chart(ctx1, config1);

  const ctx2 = document.getElementById("alltime2").getContext("2d");
  const myChart2 = new Chart(ctx2, config2);
}
