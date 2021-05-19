document.addEventListener('DOMContentLoaded', onLoad);

function onLoad(e) {
    const headers = document.querySelectorAll('.path-header');
    headers.forEach(function(header) {
        const func = `showBody("${header.id}");`;
        header.setAttribute('onclick', func);
    });
}

function showBody(parentId) {
    const childId = `${parentId}-body`;
    const child = document.getElementById(childId);
    if (child.style.display === 'block') {
        child.style.display = 'none';
    } else {
        child.style.display = 'block';
    }
}