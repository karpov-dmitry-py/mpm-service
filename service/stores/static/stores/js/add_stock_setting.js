// document.addEventListener("DOMContentLoaded", onLoad);

function checkPriority(numberInput) {
    console.log(numberInput.value);
    if (numberInput.value < 1) {
        numberInput.value = 1;
    }
    console.log(numberInput.value);
}

class UI {
    constructor() {}
}

// conditions

UI.newCondition = function() {
    const conditions = document.getElementById('conditions');
    const types = this.newConditionTypesList();
    const brands = this.newMultipleSelectList();
    
    const condition = document.createElement('div');
    condition.className = 'condition mb-5';
    condition.appendChild(types);
    condition.appendChild(brands);
    
    conditions.appendChild(condition);      
}

UI.selectOptions = function(list, selected) {
    for (let i = 0; i < list.options.length; i++) {
        let option = list.options[i];
        option.selected = selected;
    }
}

UI.selectOptionsByCmd = function(cmd, selected) {
    const wantedClassName = 'list';
    parent = cmd.parentElement.parentElement;
    for (let i = 0; i < parent.children.length; i++) {
        let child = parent.children[i];
        
        // search for class
        for (let k = 0; k < child.classList.length; k++) {
            let className = child.classList[k];
            if (className === wantedClassName) {
                this.selectOptions(child, selected); 
                return;
            }
        }
    }
}

UI.newConditionTypesList = function() {
    const container = document.createElement('div');
    container.className = 'form-group types';

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Тип условия'));
    container.appendChild(label);
    
    const typesList = document.createElement('select');
    typesList.className = 'csvselect form-control';
    
    const types = this.getConditionTypes();
    types.forEach(function(typeItem) {
        const option = document.createElement('option');
        option.value = typeItem.val;
        option.text = typeItem.text;
        typesList.appendChild(option);
    });

    container.appendChild(typesList);
    return container;
}

UI.getBrands = function() {
    result = [
        {id: 1, name: "Brand 1"},
        {id: 2, name: "Brand 2"},
        {id: 3, name: "Brand 3"},
        {id: 4, name: "Brand 4"},
        {id: 5, name: "Brand 5"},
        {id: 6, name: "Brand 6"},
        {id: 7, name: "Brand 7"},
        {id: 8, name: "Brand 8"},
        {id: 9, name: "Brand 9"},
        {id: 10, name: "Brand 10"},
    ]
    return result;
}

UI.newMultipleSelectList = function() {
    const container = document.createElement('div');
    container.className = 'form-group brands';

    const toolBar = document.createElement('div'); 
    toolBar.className = 'multiple-list-tool-bar';

    label = document.createElement('label');
    label.className = 'toolbar-lbl';
    label.appendChild(document.createTextNode('Бренд'));
    toolBar.appendChild(label);
    
    selectAll = document.createElement('span');
    selectAll.className = 'toolbar-cmd text-muted';
    selectAll.setAttribute('onclick', 'UI.selectOptionsByCmd(this, true);');
    selectAll.appendChild(document.createTextNode('выделить все'));
    toolBar.appendChild(selectAll);
    
    unselectAll = document.createElement('span');
    unselectAll.className = 'toolbar-cmd text-muted';
    unselectAll.setAttribute('onclick', 'UI.selectOptionsByCmd(this, false);');
    unselectAll.appendChild(document.createTextNode('снять выделение'));
    toolBar.appendChild(unselectAll);
    
    container.appendChild(toolBar);
    
    const list = document.createElement('select');
    list.multiple = true;
    list.size = 6;
    list.className = 'csvselect form-control list';
    
    const brands = this.getBrands();
    brands.forEach(function(brand) {
        const option = document.createElement('option');
        option.value = brand.id;
        option.text = brand.name;
        list.appendChild(option);
    });

    container.appendChild(list);
    return container;
}

UI.getConditionTypes = function() {
    const types = [
        {val: null, text: "Выберите тип условия"},
        {val: "include", text: "Включить"},
        {val: "exclude", text: "Исключить"},
        {val: "stock", text: "Остаток"},
    ]
    return types;
}


// elements

UI.getSubmitBtn = function() {
    const buttons = document.getElementsByTagName('button');
    for (let i = 0; i < buttons.length; i++) {
        let button = buttons[i];
        if (button.getAttribute('type') === 'submit') {
            return button;
        }
    }
}

UI.getMainForm = function() {
    const forms = document.getElementsByTagName('form');
    const form = forms[0];
    return form;
}