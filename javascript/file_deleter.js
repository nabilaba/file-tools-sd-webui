document.addEventListener("click", (e) => {
    if (e.target.innerText === "Delete") {
        setTimeout(() => {
            document.querySelector('[aria-label="Folder"]').dispatchEvent(new Event('change'))
        }, 500);
    }
});
