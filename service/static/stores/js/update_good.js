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
    const categorySelectElement = document.querySelector('#id_category');
    const categoryId = document.querySelector('#category_id');

    sourceObj = {
        str: '<option value="">---------</option>',
        level: 0,
    }

    // delete current options
    while (categorySelectElement.length > 0) {
        categorySelectElement.remove(categorySelectElement.length-1);
    }

    const categoriesList = document.querySelector('#categories_list');
    items = JSON.parse(categoriesList.innerText);
    build_select_list(items, sourceObj);
    categorySelectElement.innerHTML = sourceObj.str;
    for (let i = 0; i < categorySelectElement.length; i++) {
        currentItem = categorySelectElement[i];
        if (currentItem.value == categoryId.innerText ) {
            currentItem.selected = true;
            break;
        }
    }
    categoriesList.remove();
    categoryId.remove();
}