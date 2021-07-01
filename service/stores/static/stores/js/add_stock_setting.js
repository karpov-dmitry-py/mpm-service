

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

UI.newHeader = function () {
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

UI.newContent = function () {
    const content = document.createElement('div');
    content.className = 'condition-content';
    // content.appendChild(document.createTextNode('Состав этого условия:'));
    return content;
}

UI.collectConditions = function () {
    const conditionsTextArea = document.getElementById('id_content');
    items = [
        { id: 1, content: 'item 1' },
        { id: 2, content: 'item 2' },
        { id: 3, content: 'item 3' },
    ]
    result = JSON.stringify(items);
    conditionsTextArea.value = result;
}


// conditions
UI.newCondition = function () {
    const conditions = this.getConditionsDiv();
    const types = this.newTypesList();
    const header = this.newHeader();
    const content = this.newContent();

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

UI.getChildByClassName = function (parent, childClassName) {
    const children = parent.children;
    for (let i = 0; i <= children.length; i++) {
        let child = children[i];
        if (child.classList.contains(childClassName)) {
            return child;
        }
    }
}

UI.selectOptionsByCmd = function (cmd, selected) {
    const parent = cmd.parentElement.parentElement;
    const wantedClassName = 'multi-select-list';
    const selectList = this.getChildByClassName(parent, wantedClassName);
    this.selectOptions(selectList, selected);
}

UI.getContentDiv = function (conditionDiv) {
    const wantedClass = 'condition-content';
    const children = conditionDiv.children;
    for (let i = 0; i <= children.length; i++) {
        const child = children[i];
        if (child.classList.contains(wantedClass)) {
            return child;
        }
    }
}

UI.clearContentDiv = function (conditionDiv) {
    const div = this.getContentDiv(conditionDiv);
    this.clearInnerHTML(div);
}

UI.clearInnerHTML = function (el) {
    if (el === undefined || el === null) {
        return;
    }
    el.innerHTML = '';
}

UI.onTypeChange = function (list) {
    const selectedType = list.value;
    const typesDiv = list.parentElement;
    const conditionDiv = typesDiv.parentElement;

    // always reset content
    this.clearContentDiv(conditionDiv);

    if (selectedType === 'null') {
        return;
    }

    const conditionContentDiv = this.getContentDiv(conditionDiv);

    if (selectedType === 'include' || selectedType === 'exclude') {
        const InclExclTypesList = this.newInclExclTypesList();
        conditionContentDiv.appendChild(InclExclTypesList);
        console.log("вкл/выкл");
    } else if (selectedType === 'stock') {
        console.log("остаток");
    }

    const fieldsList = this.newFieldsList();
    conditionContentDiv.appendChild(fieldsList);
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

UI.newNumberInput = function (className, labelStr) {
    const container = document.createElement('div');
    container.className = `form-group ${className}`;

    label = document.createElement('label');
    label.appendChild(document.createTextNode(labelStr));
    container.appendChild(label);

    const input = document.createElement('input');
    input.className =
        container.appendChild(input);
    return container;
}

UI.newTypesList = function () {
    const container = document.createElement('div');
    container.className = 'form-group types';

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Тип условия'));
    container.appendChild(label);

    const types = this.getConditionTypes();
    const typesList = this.newOptionList(types);
    typesList.setAttribute('onchange', 'UI.onTypeChange(this);');
    container.appendChild(typesList);

    return container;
}

UI.getConditionCurrentType = function (conditionDiv) {
    const children = conditionDiv.children;

    // get types div
    for (let i = 0; i < children.length; i++) {
        let child = children[i];
        if (child.classList.contains('types')) {

            // get select list
            let innerChildren = child.children;
            for (let ii = 0; ii < innerChildren.length; ii++) {
                let innerChild = innerChildren[ii];
                if (innerChild.classList.contains('select-list')) {
                    return innerChild.value;
                }
            }
        }
    }
}


UI.newOptionList = function (src) {
    const selectList = document.createElement('select');
    selectList.className = 'csvselect form-control select-list';
    src.forEach(function (item) {
        const option = document.createElement('option');
        option.value = item.val;
        option.text = item.text;
        selectList.appendChild(option);
    });
    return selectList;
}

UI.onFieldChange = function (fieldsSelectList) {
    const selectedField = fieldsSelectList.value;
    const fieldContent = fieldsSelectList.nextSibling;
    this.clearInnerHTML(fieldContent);

    let items = null;
    let content = null;

    // get type of current condition
    // const conditionDiv = fieldsSelectList.parentElement.parentElement.parentElement;
    // const currentType = this.getConditionCurrentType(conditionDiv);

    if (selectedField === 'brand') {
        items = this.getBrands();
        content = this.newMultiSelectList('brands', 'Бренды', items);
        fieldContent.appendChild(content);

    } else if (selectedField === 'warehouse') {
        items = this.getWarehouses();
        content = this.newMultiSelectList('warehouses', 'Склады', items);
        fieldContent.appendChild(content);
    } else if (selectedField === 'cat') {
        items = this.getCats();
        content = this.newMultiSelectList('cats', 'Категории', items);
        const selectList = this.getChildByClassName(content, 'multi-select-list');
        selectList.innerHTML = this.buildTreeSelectList(items);
        fieldContent.appendChild(content);
    } else {
        fieldContent.innerHTML = selectedField;
    }
}

UI.newFieldsList = function () {
    const container = document.createElement('div');
    container.className = 'form-group fields';

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Поле условия'));
    container.appendChild(label);

    const fields = this.getConditionFields();
    const fieldsSelectList = this.newOptionList(fields);
    fieldsSelectList.setAttribute('onchange', 'UI.onFieldChange(this);');

    container.appendChild(fieldsSelectList);

    const fieldContent = document.createElement('div');
    fieldContent.className = 'form-group field-content';
    container.appendChild(fieldContent);

    return container;
}

UI.newMultiSelectList = function (className, labelStr, items) {
    const container = document.createElement('div');
    container.className = `form-group mt-3 ${className}`;

    const toolBar = document.createElement('div');
    toolBar.className = 'multiple-list-tool-bar';

    label = document.createElement('label');
    label.className = 'toolbar-lbl';
    label.appendChild(document.createTextNode(labelStr));
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
    list.className = 'csvselect form-control multi-select-list';

    items.forEach(function (item) {
        const option = document.createElement('option');
        option.value = item.val;
        option.text = item.text;
        list.appendChild(option);
    });

    container.appendChild(list);
    return container;
}

UI.fromJson = function (el) {
    const result = JSON.parse(el.innerHTML);
    return result;
}

UI.getConditionTypes = function () {
    const el = document.getElementById('condition_types');
    return this.fromJson(el);
}

UI.getInclExclTypes = function () {
    const el = document.getElementById('include_types');
    return this.fromJson(el);
}

UI.getConditionFields = function () {
    const el = document.getElementById('condition_fields');
    return this.fromJson(el);
}

UI.getBrands = function () {
    const el = document.getElementById('brands');
    return this.fromJson(el);
}

UI.getCats = function () {
    const el = document.getElementById('cats');
    return this.fromJson(el);
}

UI.getWarehouses = function () {
    const el = document.getElementById('warehouses');
    return this.fromJson(el);
}

// TODO - goods

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

UI.buildTreeSelectList = function (items) {
    const initialData = {
        str: '',
        level: 0,
    }
    buildTreeSelectList(items, initialData)
    return initialData.str;
}

function buildTreeSelectList(items, initialData) {
    items.forEach(function (item) {
        const level = initialData.level;
        const levelStrBaseChar = '&emsp;';
        let levelStr = '';
        let i = 1;
        while (i <= level) {
            i++;
            levelStr += levelStrBaseChar;
        }
        const label = levelStr + item.name;
        option = `<option value=${item.id}>${label}</option>`;
        initialData.str += option;
        if ('childs' in item) {
            initialData.level += 1;
            buildTreeSelectList(item.childs, initialData)
            initialData.level -= 1;
        }
    });
}

class Storage {
    constructor() { }
}

Storage.set = function (key, val) {
    sessionStorage.setItem(key, toJson(val))
    console.log('saved data to storage.');
}

Storage.get = function (key) {
    const val = sessionStorage.getItem(key);
    if (val !== null && val !== undefined) {
        console.log('read data from storage.');
        return fromJson(val);
    }
    console.log('no data found in storage.');
}

class Api {
    constructor() { }
}

Api.callback = function (result) {
    console.log(result);
    const key = "goods";
    Storage.set(key, result);
    const goods = Storage.get(key);
    console.log(goods);

}

Api.get = function (url) {
    fetch(url)
        .then((response) => {
            if (response.ok) {
                return response.json();
            } else {
                console.log(`API call returned ${response.status} response`);
                // return response.text();
            }
        })
        .then((data) => {
            this.callback(data);
            return;
        })
        .catch((error) => {
            console.log(`API call returned an error: ${error}`);
        });
}

function fromJson(src) {
    const result = JSON.parse(src);
    return result;
}

function toJson(src) {
    const result = JSON.stringify(src);
    return result;
}


function testAPI(url) {
    Api.get(url);
}

const testUrl = "/goods/user";
document.addEventListener("DOMContentLoaded", testAPI(testUrl));

