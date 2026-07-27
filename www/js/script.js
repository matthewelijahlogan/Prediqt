window.addEventListener("load", () => {
  const splash = document.getElementById("splashScreen");
  if (!splash) return;

  setTimeout(() => {
    splash.style.opacity = 0;
    splash.style.visibility = "hidden";
    setTimeout(() => splash.remove(), 700);
  }, 900);
});

