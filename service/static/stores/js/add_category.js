document.addEventListener('DOMContentLoaded', onLoad);

function onLoad(e) {
    const parentSelectElement = document.querySelector('#id_parent');

    // delete current options
    while (parentSelectElement.length > 0) {
        parentSelectElement.remove(parentSelectElement.length-1);
    }
    const parentSelectList = document.querySelector('#parent_select_list');
    items = JSON.parse(parentSelectList.innerText);

    sourceObj = {
        str: '<option value="" selected="">---------</option>',
        level: 0,
    }
    build_select_list(items, sourceObj);
    parentSelectElement.innerHTML = sourceObj.str;
    parentSelectList.remove();
}

function build_select_list(items, sourceObj) {
    items.forEach( function(item) {
        const level = sourceObj.level;
        const levelStrBaseChar = '&emsp;';
        let levelStr = '';
        let i = 1;
        while (i <= level) {
            i++;
            levelStr += levelStrBaseChar;
        }
        const label = levelStr + item.name;
        option = `<option value=${item.id}>${label}</option>`;
        sourceObj.str += option;
        if ('childs' in item) {
            sourceObj.level += 1;
            build_select_list(item.childs, sourceObj)
            sourceObj.level -= 1;
        }
    });
}