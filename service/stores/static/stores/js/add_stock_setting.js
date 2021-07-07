const searchResultsHeader = 'Найденные товары';
const savedGoodsHeader = 'Добавленные к условию товары';
const savedGoodsListClass = 'saved-goods-list';
const toolbarLabel = 'toolbar-lbl';

const multiselectListClass = 'multi-select-list';
const goodsSearchResultsSelectAllCmdClass = 'goods-toolbar-cmd';
const minGoodsSearchInputLength = 3;

function validateNumberInputMinValue(numberInput, minValue) {
    if (numberInput.value < minValue) {
        numberInput.value = minValue;
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
    return content;
}

UI.collectConditions = function () {
    const conditionsTextArea = document.getElementById('id_content');
    
    const conditions = [];
    const conditionsDiv = this.getConditionsDiv();
    const includeTypes = ["include", "exclude"]


    for (let i = 0; i < conditionsDiv.children.length; i++) {
        
        // put current conditron content into this object
        const conditionObject = {
            type: null,
            field: null,
            values: null,
            includeType: null,
            minStock: null,
        } 
        
        const condition = conditionsDiv.children[i];
        let currentType = this.getConditionCurrentType(condition);
        if (currentType === 'null') {
            currentType = null;
        }
        conditionObject.type = currentType;

        const conditionContentDiv =  

        

        

        if (currentType === null) {
            conditions.push(conditionObject);
            continue;        }

        conditions.push(conditionObject);
    }
    
    result = JSON.stringify(conditions);
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
    const selectList = this.getChildByClassName(parent, multiselectListClass);
    this.selectOptions(selectList, selected);

    if (selected && cmd.classList.contains(goodsSearchResultsSelectAllCmdClass)) {
        this.onSelectSearchResult(selectList);
    }
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
    } else if (selectedType === 'stock') {
        const stockInput = this.newInput(
            'number',
            'number-input',
            'Остаток по полю условия больше или равен',
            'onkeyup',
            'validateNumberInputMinValue(this, 1);',
        );
        conditionContentDiv.appendChild(stockInput);
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

UI.newInput = function (type, className, labelStr, eventName, eventHandler) {
    const types = {
        text: 'textinput',
        number: 'numberinput',
    }

    const container = document.createElement('div');
    container.className = `form-group mt-3 ${className}`;

    label = document.createElement('label');
    label.appendChild(document.createTextNode(labelStr));
    container.appendChild(label);

    const input = document.createElement('input');
    input.className = `${types[type]} form-control`;
    input.type = type;

    if (eventName !== null) {
        input.setAttribute(eventName, `${eventHandler}`);
    }

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
        const selectList = this.getChildByClassName(content, multiselectListClass);
        selectList.innerHTML = this.buildTreeSelectList(items);
        fieldContent.appendChild(content);

    } else if (selectedField === 'good') {
        const searchInput = this.newInput(
            'text',
            'text-input',
            `Поиск товаров по коду/наименованию (мин. ${minGoodsSearchInputLength} символа)`,
            'oninput',
            'UI.onSearchInput(this);');
        fieldContent.appendChild(searchInput);

        const resultsBox = this.newMultiSelectList('goods', searchResultsHeader, [], true, true);
        const resultsList = this.getChildByClassName(resultsBox, multiselectListClass);
        resultsList.setAttribute('onchange', 'UI.onSelectSearchResult(this);');
        fieldContent.appendChild(resultsBox);

        const savedGoodsBox = this.newUL('saved-goods', savedGoodsHeader, [], true);
        fieldContent.appendChild(savedGoodsBox);

    } else {
        fieldContent.innerHTML = selectedField;
    }
}

UI.getListSelectedOptions = function (list) {
    const items = [];
    for (let i = 0; i < list.length; i++) {
        const option = list.options[i];
        if (option.selected) {
            const item = { val: option.value, text: option.text }
            items.push(item);
        }
    }
    return items;
}

UI.onSelectSearchResult = function (list) {
    const selectedItems = this.getListSelectedOptions(list);
    const listBox = list.parentElement;
    const savedGoodsBox = listBox.nextSibling;
    const savedGoodsList = this.getChildByClassName(savedGoodsBox, savedGoodsListClass);
    this.appendToUL(savedGoodsList, selectedItems);

    const savedGoodsToolbar = savedGoodsList.previousSibling;
    const savedGoodsLabel = this.getChildByClassName(savedGoodsToolbar, toolbarLabel);
    this.setSavedGoodsHeader(savedGoodsLabel, savedGoodsList.children.length);
}

UI.clearSelectList = function (list) {
    while (list.length > 0) {
        list.remove(list[0]);
    }
}

UI.setSavedGoodsHeader = function (el, itemsCount) {
    let header = '';
    if (itemsCount === 0) {
        header = savedGoodsHeader;
    } else {
        header = `${savedGoodsHeader} (${itemsCount})`;
    }
    el.innerHTML = header;
}

UI.setSearchResultsHeaderText = function (el, matchedCount) {
    let header = '';
    if (matchedCount === 0) {
        header = searchResultsHeader;
    } else {
        header = `${searchResultsHeader} (${matchedCount})`;
    }
    el.innerHTML = header;
}

UI.onSearchInput = function (el) {
    // delete current items
    const resultsDiv = el.parentElement.nextSibling;
    const resultsList = this.getChildByClassName(resultsDiv, multiselectListClass);
    this.clearSelectList(resultsList);

    const toolbarDiv = resultsList.previousSibling;
    const label = this.getChildByClassName(toolbarDiv, toolbarLabel);

    const input = el.value.toLowerCase();
    if (input.length < minGoodsSearchInputLength) {
        resultsList.size = 1;
        this.setSearchResultsHeaderText(label, 0);
        return;
    }

    const items = Storage.get('goods');
    let matched = 0;
    items.forEach(function (item) {
        if (item.sku.toLowerCase().includes(input) || item.name.toLowerCase().includes(input)) {
            matched++;
            const option = document.createElement('option');
            option.value = item.sku;
            option.text = `(${item.sku}) ${item.name}`;
            resultsList.appendChild(option);
        }
    });
    resultsList.size = this.getSelectListWantedSize(matched);
    this.setSearchResultsHeaderText(label, matched);
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

UI.getDefaultSelectListSize = function () {
    return 10;
}

UI.getSelectListWantedSize = function (itemsLength) {
    return Math.min(this.getDefaultSelectListSize(), itemsLength + 1);
}

UI.newMultiSelectList = function (className, labelStr, items, isWide) {
    const container = document.createElement('div');
    container.className = `form-group mt-3 ${className}`;

    if (isWide) {
        container.classList.add('wide');
    }

    const toolBar = document.createElement('div');
    toolBar.className = 'multiple-list-tool-bar';

    label = document.createElement('label');
    label.className = toolbarLabel;
    label.appendChild(document.createTextNode(labelStr));
    toolBar.appendChild(label);

    selectAll = document.createElement('span');
    selectAll.className = `toolbar-cmd text-muted ${goodsSearchResultsSelectAllCmdClass}`;
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

    const listSize = this.getSelectListWantedSize(items.length);

    if (className === 'cats') {
        list.size = this.getDefaultSelectListSize();
    } else {
        list.size = listSize;
    }

    list.className = `csvselect form-control ${multiselectListClass}`;

    items.forEach(function (item) {
        const option = document.createElement('option');
        option.value = item.val;
        option.text = item.text;
        list.appendChild(option);
    });

    container.appendChild(list);
    return container;
}

UI.newUL = function (className, labelStr, items, isWide) {
    const container = document.createElement('div');
    container.className = `form-group mt-3 ${className}`;

    if (isWide) {
        container.classList.add('wide');
    }

    const toolBar = document.createElement('div');
    toolBar.className = 'multiple-list-tool-bar';

    label = document.createElement('label');
    label.className = toolbarLabel;
    label.appendChild(document.createTextNode(labelStr));
    toolBar.appendChild(label);

    deleteAll = document.createElement('span');
    deleteAll.className = 'toolbar-cmd text-muted';
    deleteAll.setAttribute('onclick', 'UI.clearUL(this);');
    deleteAll.appendChild(document.createTextNode('удалить все'));
    toolBar.appendChild(deleteAll);
    container.appendChild(toolBar);

    const list = document.createElement('ul');
    list.className = `list-group ${className}-list`;
    this.appendToUL(list, items);

    container.appendChild(list);
    return container;
}

UI.clearUL = function (dltElement) {
    const toolbar = dltElement.parentElement;
    const list = toolbar.nextSibling;
    this.clearInnerHTML(list);
    
    const toolbarLbl = this.getChildByClassName(toolbar, toolbarLabel);
    this.setSavedGoodsHeader(toolbarLbl, list.children.length);
}

UI.getValuesFromUL = function (list) {
    const vals = [];
    for (let i = 0; i < list.children.length; i++) {
        const child = list.children[i];
        vals.push(child.getAttribute('val'));
    }
    return vals;
}

UI.appendToUL = function (list, items) {
    currentVals = this.getValuesFromUL(list);
    for (let i = 0; i < items.length; i++) {

        const item = items[i];
        if (currentVals.includes(item.val)) {
            continue;
        }

        const li = document.createElement('li');
        li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center li-small';
        li.setAttribute('val', item.val);
        li.appendChild(document.createTextNode(item.text));

        const span = document.createElement('span');
        span.className = 'badge badge-light badge-pill text-muted li-delete';
        span.appendChild(document.createTextNode('X'));
        span.setAttribute('title', 'удалить этот товар');
        span.setAttribute('onclick', 'UI.deleteLI(this)');

        li.appendChild(span);
        list.appendChild(li);
    }
}

UI.deleteLI = function (span) {
    const li = span.parentElement;
    const list = li.parentElement;
    list.removeChild(li);

    const searchResultsBox = list.previousSibling;
    const searchResultsLabel = this.getChildByClassName(searchResultsBox, toolbarLabel);
    this.setSavedGoodsHeader(searchResultsLabel, list.children.length);
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
}

Storage.get = function (key) {
    const val = sessionStorage.getItem(key);
    if (val !== null && val !== undefined) {
        return fromJson(val);
    }
    console.log('no data found in storage!');
}

class Api {
    constructor() { }
}

Api.callback = function (result) {
    const key = "goods";
    Storage.set(key, result);
}

Api.get = function (url) {
    fetch(url)
        .then((response) => {
            if (response.ok) {
                return response.json();
            } else {
                console.log(`API call returned ${response.status} response`);
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

