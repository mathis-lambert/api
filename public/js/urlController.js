const submit = document.getElementById("submit");
const url = document.getElementById("url");
const result = document.getElementById("shortUrl");
const card = document.querySelector(".main-card");
url.addEventListener("keyup", (e) => {
  if (e.key === "Enter") {
    submit.click();
  }
});
submit.addEventListener("click", async () => {
  submit.classList.add("loading");
  card.classList.remove("result");

  await fetch("/url", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: url.value }),
  })
    .then((res) => res.json())
    .then((data) => {
      computeResult(data);
      submit.classList.remove("loading");
      submit.classList.add("success");
    })
    .catch((err) => {
      console.error(err);
      result.value = "Une erreur est survenue :" + err;
      submit.classList.remove("loading");
      submit.classList.add("error");
    });

  url.value = "";
});

function computeResult(data) {
  card.classList.add("result");
  if (data.error) {
    result.value = "Une erreur est survenue :" + err;
  } else {
    result.value = "api.mathislambert.fr/url/" + data.short_url;
    document.querySelector("#accessLink").href = "https://" + result.value;

    const copyButton = document.getElementById("copy");
    copyButton.addEventListener("click", async () => {
      let value = result.value;
      try {
        await navigator.clipboard.writeText(value);
        console.log("Copied to clipboard");
        copyButton.classList.add("success");
        submit.classList.remove("success");

        setTimeout(() => {
          copyButton.classList.remove("success");
          submit.classList.remove("success");
        }, 2000);
      } catch (err) {
        console.error("Failed to copy: ", err);
        copyButton.classList.add("error");
      }
    });
  }
}
