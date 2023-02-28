Chart.defaults.color = "white";

const config1 = {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Temperature",
        tension: 0.5,

        data: [],
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        borderColor: "rgba(255, 99, 132, 1)",
      },
      {
        label: "Humidity",
        tension: 0.5,

        data: [],
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
    labels: [],
    datasets: [
      {
        label: "Pressure",
        tension: 0.5,

        data: [],
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

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${day}/${month} ${hours}:${minutes}`;
}

async function initData(mindate, maxdate) {
  let allTimeData = [];

  let response = await fetch("./iot/list/" + mindate + "-" + maxdate);
  let data = await response.json();

  allTimeData = data;
  allTimeData.map((item) => (item.timestamp = formatTimestamp(item.timestamp)));
  allTimeData.map(
    (item) =>
      (item.values.temperature = parseFloat(item.values.temperature) - 12)
  );

  displayChart(allTimeData);
}

function displayChart(data) {
  let temperature = data.map((item) => item.values.temperature);
  let humidity = data.map((item) => item.values.humidity);
  let pressure = data.map((item) => item.values.pressure);
  let labels = data.map((item) => item.timestamp);

  console.log(temperature);
  console.log(humidity);
  console.log(pressure);

  myChart1.data.labels = labels;
  myChart1.data.datasets[0].data = temperature;
  myChart1.data.datasets[1].data = humidity;
  myChart1.update();

  myChart2.data.labels = labels;
  myChart2.data.datasets[0].data = pressure;
  myChart2.update();

  const temperatureHTML = document.getElementById("temperature");
  const humidityHTML = document.getElementById("humidity");
  const pressureHTML = document.getElementById("pressure");

  temperatureHTML.innerHTML = temperature[temperature.length - 1] + "°C";
  humidityHTML.innerHTML = humidity[humidity.length - 1] + " %";
  pressureHTML.innerHTML = pressure[pressure.length - 1] + " hPa";
}

let mindate = "";
let maxdate = "";

window.onload = () => {
  mindate = new Date().getTime() - 3600000;
  maxdate = new Date().getTime();

  initData(mindate, maxdate);
};

// button gestion
const refresh = document.getElementById("refresh");
refresh.addEventListener("click", () => {
  maxdate = new Date().getTime();
  initData(mindate, maxdate);
});

const alltime = document.getElementById("alltime");
alltime.addEventListener("click", () => {
  mindate = new Date("2021-01-01").getTime();
  maxdate = new Date().getTime();
  initData(mindate, maxdate);
});

const lasthour = document.getElementById("lasthour");
lasthour.addEventListener("click", () => {
  mindate = new Date().getTime() - 3600000;
  maxdate = new Date().getTime();
  initData(mindate, maxdate);
});

const lastday = document.getElementById("lastday");
lastday.addEventListener("click", () => {
  mindate = new Date().getTime() - 86400000;
  maxdate = new Date().getTime();
  initData(mindate, maxdate);
});

const lastweek = document.getElementById("lastweek");
lastweek.addEventListener("click", () => {
  mindate = new Date().getTime() - 604800000;
  maxdate = new Date().getTime();
  initData(mindate, maxdate);
});

const lastmonth = document.getElementById("lastmonth");
lastmonth.addEventListener("click", () => {
  mindate = new Date().getTime() - 2629800000;
  maxdate = new Date().getTime();
  initData(mindate, maxdate);
});
