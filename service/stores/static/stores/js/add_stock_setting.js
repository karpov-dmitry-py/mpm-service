// document.addEventListener("DOMContentLoaded", onLoad);

function checkPriority(numberInput) {
    if (numberInput.value < 1) {
        numberInput.value = 1;
    }
}

function scrollToBottom() {
    window.scrollTo(0, document.body.scrollHeight);
}

function scrollToTop() {
    window.scrollTo(0, 0);
}

class UI {
    constructor() { }
}

UI.newConditionHeader = function () {
    const header = document.createElement('div');
    header.className = 'condition-header row mb-4';

    const headerDiv = document.createElement('div');
    headerDiv.className = 'col-10 condition-header-bar';

    let span = document.createElement('span');
    span.className = 'condition-header-text';
    const headerText = this.getConditionHeaderText(this.getConditionsCount() + 1);
    const headerTextNode = document.createTextNode(headerText);
    span.appendChild(headerTextNode);
    headerDiv.appendChild(span);
    header.appendChild(headerDiv);

    const deleteDiv = document.createElement('div');
    deleteDiv.className = 'col-2 delete-condition-bar';

    span = document.createElement('span');
    span.className = 'delete-condition-btn text-muted';
    span.appendChild(document.createTextNode('удалить условие'));
    span.setAttribute('title', 'удалить это условие');
    span.setAttribute('onclick', 'UI.deleteCondition(this);');
    deleteDiv.appendChild(span);

    header.appendChild(deleteDiv);
    return header;
}

UI.deleteCondition = function (deleteBtn) {
    const condition = deleteBtn.parentElement.parentElement;
    const conditions = condition.parentElement;
    conditions.remove(condition);
    this.enumerateConditions();
}

UI.getConditionsCount = function () {
    const conditions = this.getConditionsDiv();
    const result = conditions.children.length;
    return result;
}

UI.getConditionHeaderText = function (number) {
    const result = `Условие № ${number}`;
    return result;
}

UI.enumerateConditions = function () {
    const conditionsHeaders = document.querySelectorAll('.condition-header-text');
    if (conditionsHeaders.length === 0) {
        return;
    }
    conditionsHeaders.forEach(function (header, index) {
        header.innerHTML = UI.getConditionHeaderText(index + 1);
    });
}

UI.getConditionsDiv = function () {
    return document.getElementById('conditions');
}

// conditions
UI.newCondition = function () {
    const conditions = this.getConditionsDiv();
    const types = this.newConditionTypesList();
    // const brands = this.newMultipleSelectList();
    const header = this.newConditionHeader();
    const content = document.createElement('div')
    content.className = 'condition-content';
    content.appendChild(document.createTextNode('Состав условия:'));

    const condition = document.createElement('div')
    condition.className = 'condition mb-3';

    condition.appendChild(header);
    condition.appendChild(types);
    condition.appendChild(content);

    conditions.appendChild(condition);
    scrollToBottom();
}

UI.selectOptions = function (list, selected) {
    for (let i = 0; i < list.options.length; i++) {
        let option = list.options[i];
        option.selected = selected;
    }
}

UI.selectOptionsByCmd = function (cmd, selected) {
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

UI.getConditionContentDiv = function (conditionDiv) {
    const wantedClass = 'condition-content';
    const children = conditionDiv.children;
    for (let i = 0; i <= children.length; i++) {
        const child = children[i];
        if (child.classList.contains(wantedClass)) {
            return child;
        }
    }
}

UI.clearConditionContentDiv = function (conditionDiv) {
    const div = this.getConditionContentDiv(conditionDiv);
    this.clearInnerHTML(div);
}

UI.clearInnerHTML = function (el) {
    if (el === undefined || el === null) {
        return;
    }
    el.innerHTML = '';
}

UI.handleConditionTypeChoice = function (list) {
    const selectedType = list.value;
    const typesDiv = list.parentElement;
    const conditionDiv = typesDiv.parentElement;
    
    // always reset content
    this.clearConditionContentDiv(conditionDiv);

    if (selectedType === 'null') {
        return;
    }


    const fieldsList = this.newConditionFieldsList();
    const conditionContentDiv = this.getConditionContentDiv(conditionDiv);
    conditionContentDiv.appendChild(fieldsList);

    if (selectedType === 'include' || selectedType === 'exclude') {
        const InclExclTypesList = this.newInclExclTypesList();
        conditionContentDiv.appendChild(InclExclTypesList);
        console.log("вкл/выкл");
    } else if (selectedType === 'stock') {
        console.log("остаток");
    }
}

UI.newInclExclTypesList = function () {
    const container = document.createElement('div');
    container.className = 'form-group incl-excl-types';

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Остаток по полю условия'));
    container.appendChild(label);

    const types = this.getInclExclTypes();
    const select = this.newOptionList(types);
    container.appendChild(select);
    return container;
}

UI.newConditionTypesList = function () {
    const container = document.createElement('div');
    container.className = 'form-group types';

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Тип условия'));
    container.appendChild(label);

    const typesList = document.createElement('select');
    typesList.className = 'csvselect form-control';
    typesList.setAttribute('onchange', 'UI.handleConditionTypeChoice(this);');

    const types = this.getConditionTypes();
    types.forEach(function (typeItem) {
        const option = document.createElement('option');
        option.value = typeItem.val;
        option.text = typeItem.text;
        typesList.appendChild(option);
    });

    container.appendChild(typesList);
    return container;
}

UI.newOptionList = function (src) {
    const select = document.createElement('select');
    select.className = 'csvselect form-control';

    src.forEach(function (item) {
        const option = document.createElement('option');
        option.value = item.val;
        option.text = item.text;
        select.appendChild(option);
    });
    return select;
}

UI.newConditionFieldsList = function () {
    const container = document.createElement('div');
    container.className = 'form-group fields';

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Поле условия'));
    container.appendChild(label);

    const fieldsList = document.createElement('select');
    fieldsList.className = 'csvselect form-control';
    // fieldsList.setAttribute('onchange', 'UI.handleConditionTypeChoice(this);');

    const fields = this.getConditionFields();
    fields.forEach(function (field) {
        const option = document.createElement('option');
        option.value = field.val;
        option.text = field.text;
        fieldsList.appendChild(option);
    });

    container.appendChild(fieldsList);
    return container;
}

UI.newMultipleSelectList = function () {
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
    list.size = 10;
    list.className = 'csvselect form-control list';

    const brands = this.getBrands();
    brands.forEach(function (brand) {
        const option = document.createElement('option');
        option.value = brand.val;
        option.text = brand.text;
        list.appendChild(option);
    });

    container.appendChild(list);
    return container;
}

UI.parseJson = function (el) {
    const content = JSON.parse(el.innerHTML);
    return content;
}

UI.getConditionTypes = function () {
    const el = document.getElementById('condition_types');
    return this.parseJson(el);
}

UI.getInclExclTypes = function () {
    const el = document.getElementById('include_types');
    return this.parseJson(el);
}

UI.getConditionFields = function () {
    const el = document.getElementById('condition_fields');
    return this.parseJson(el);
}

UI.getBrands = function () {
    const el = document.getElementById('brands');
    return this.parseJson(el);
}

// elements
UI.getSubmitBtn = function () {
    const buttons = document.getElementsByTagName('button');
    for (let i = 0; i < buttons.length; i++) {
        let button = buttons[i];
        if (button.getAttribute('type') === 'submit') {
            return button;
        }
    }
}

UI.getMainForm = function () {
    const forms = document.getElementsByTagName('form');
    const form = forms[0];
    return form;
}