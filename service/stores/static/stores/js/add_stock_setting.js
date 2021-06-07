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
    
    const condition = document.createElement('div');
    condition.className = 'condition mb-5';

    condition.appendChild(types);
    conditions.appendChild(condition);
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