// Inject this into index.html to log clicked elements
const script = document.createElement('script');
script.innerHTML = `
document.addEventListener('mousedown', (e) => {
    let el = document.elementFromPoint(e.clientX, e.clientY);
    console.log('[DEBUG CLICK] x: ' + e.clientX + ', y: ' + e.clientY + ' -> ' + el.id + ' | ' + el.className + ' | ' + el.tagName);
}, true);
`;
document.head.appendChild(script);
