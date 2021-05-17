function showBody(parentId) {
    const childId = `${parentId}-body`;
    const child = document.getElementById(childId);
    if (child.style.display === 'block') {
        child.style.display = 'none';
    } else {
        child.style.display = 'block';
    }
}