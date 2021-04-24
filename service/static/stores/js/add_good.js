document.addEventListener('DOMContentLoaded', onLoad);

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

function filterBrandSelectList () {
    const brandChoiceList = document.querySelector('#id_brand');
    let allowedBrandsDiv = document.querySelector('#brands');
    allowedBrands = JSON.parse(allowedBrandsDiv.innerText);
    const choices = brandChoiceList.children;
    let deletedNodesCount = 0;
    let choicesLength = choices.length;
    for (let i=0; i<choicesLength; i++ ) {
        let index = i-deletedNodesCount;
        let item = choices[index];
        console.log('item: ', item);
       if (item.value !== "" && !allowedBrands.includes(item.value)) {
            console.log('option to remove: ', item.value);   
            brandChoiceList[index] = null;
            deletedNodesCount++;
       }
    }
    allowedBrandsDiv.parentElement.removeChild(allowedBrandsDiv);
}

function onLoad(e) {
    // filterBrandSelectList();
    const categorySelectElement = document.querySelector('#id_category');

    // delete current options
    while (categorySelectElement.length > 0) {
        categorySelectElement.remove(categorySelectElement.length-1);
    }
    const categoriesList = document.querySelector('#categories_list');
    items = JSON.parse(categoriesList.innerText);

    sourceObj = {
        str: '<option value="" selected="">---------</option>',
        level: 0,
    }
    build_select_list(items, sourceObj);
    categorySelectElement.innerHTML = sourceObj.str;
    categoriesList.remove();
}