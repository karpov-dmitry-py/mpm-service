document.addEventListener('DOMContentLoaded', onLoad);

function build_select_list(items, sourceObj) {
    items.forEach( function(item) {
        const selectedValueTemplate = `selected=""`;
        const level = sourceObj.level;
        const levelStrBaseChar = '&emsp;';
        let levelStr = '';
        let i = 1;
        while (i <= level) {
            i++;
            levelStr += levelStrBaseChar;
        }
        const label = levelStr + item.name;
        let itemSelectedFiller = '';
        if (sourceObj.currentValue === item.id) {
            itemSelectedFiller = selectedValueTemplate;
        }
        option = `<option value=${item.id} ${itemSelectedFiller}>${label}</option>`;
        sourceObj.str += option;
        if ('childs' in item) {
            sourceObj.level += 1;
            build_select_list(item.childs, sourceObj)
            sourceObj.level -= 1;
        }
    });
}

function onLoad(e) {
    const parentSelectElement = document.querySelector('#id_parent');
    const parentId = document.querySelector('#parent_id');

    sourceObj = {
        str: '<option value="">---------</option>',
        level: 0,
    }

    // delete current options
    while (parentSelectElement.length > 0) {
        parentSelectElement.remove(parentSelectElement.length-1);
    }

    const parentSelectList = document.querySelector('#parent_select_list');
    items = JSON.parse(parentSelectList.innerText);
    build_select_list(items, sourceObj);
    parentSelectElement.innerHTML = sourceObj.str;
    for (let i = 0; i < parentSelectElement.length; i++) {
        currentItem = parentSelectElement[i];
        if (currentItem.value == parent_id.innerText ) {
            currentItem.selected = true;
            break;
        }
    }
    parentSelectList.remove();
    parentId.remove();
}