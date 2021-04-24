function checkPhone(element) {
    const max_chars = 10;
    if(element.value.length > max_chars) {
        element.value = element.value.substr(0, max_chars);
    }
}