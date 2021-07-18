const getGoodsApiUrl = "/goods/user";
const searchResultsHeader = 'Найденные товары';
const savedGoodsHeader = 'Добавленные к условию товары';
const minGoodsSearchInputLength = 3;

const toolbarLabel = 'toolbar-lbl';
const savedGoodsDivClass = 'saved-goods';
const savedGoodsListClass = 'saved-goods-list';
const inclExclTypesClass = 'incl-excl-types';
const minStockClass = 'min-stock';
const conditionContentClass = 'condition-content';
const fieldContentClass = 'field-content';
const selectListClass = 'select-list';
const multiselectListClass = 'multi-select-list';
const goodsSearchResultsToolbarCmdClass = 'goods-toolbar-cmd';

const includeTypes = ["include", "exclude",];
const fldSelectTypes = ["warehouse", "cat", "brand",];
const fldSelectListClasses = {
    warehouse: "warehouses",
    cat: "cats",
    brand: "brands",
}

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
    span.setAttribute('onclick', 'UI.newDeleteQuestion(this);');
    deleteDiv.appendChild(span);

    header.appendChild(deleteDiv);
    return header;
}

UI.onDeleteConfirm = function (btn) {

}

UI.onDeleteCancel = function (btn) {
    const currenDeleteDiv = btn.parentElement;
    const header = currenDeleteDiv.previousSibling;
    const deleteDiv = this.getChildByClassName(header, 'delete-condition-bar');
    const deleteSpan = this.getChildByClassName(deleteDiv, 'delete-condition-btn');
    deleteSpan.style.display = 'inline';
    currenDeleteDiv.parentElement.removeChild(currenDeleteDiv);
}

UI.newDeleteQuestion = function (target) {
    target.style.display = 'none';

    const div = document.createElement('div');
    div.className = 'd-flex justify-content-center border mb-3';

    const cancelBtn = document.createElement('a');
    cancelBtn.setAttribute('href', '#');
    cancelBtn.setAttribute('onclick', 'UI.onDeleteCancel(this);');
    cancelBtn.className = 'btn btn-outline-secondary setting-btn';
    cancelBtn.appendChild(document.createTextNode('Отменить удаление'));
    div.appendChild(cancelBtn);

    const deleteBtn = document.createElement('a');
    deleteBtn.setAttribute('href', '#');
    deleteBtn.setAttribute('onclick', 'UI.deleteCondition(this);');
    deleteBtn.className = 'btn btn-outline-danger setting-btn';
    deleteBtn.appendChild(document.createTextNode('Удалить условие'));
    div.appendChild(deleteBtn);

    const header = target.parentElement.parentElement;
    const condition = header.parentElement;
    condition.insertBefore(div, header.nextSibling);
}

UI.deleteCondition = function (deleteBtn) {
    const condition = deleteBtn.parentElement.parentElement;
    const conditions = condition.parentElement;
    conditions.removeChild(condition);
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
    content.className = conditionContentClass;
    return content;
}

UI.hideConditionsTextArea = function () {
    const conditionsTextArea = document.getElementById('id_content');
    if (conditionsTextArea === null) {
        return;
    }
    conditionsTextArea.parentElement.parentElement.classList.add('hidden');
}

UI.buildConditions = function () {
    const conditionsTextArea = document.getElementById('id_content');
    if (conditionsTextArea === null) {
        return;
    }

    const json = conditionsTextArea.value;
    if (!isJSON(json)) {
        return;
    }
    const conditions = fromJson(json);
    if (conditions.length === 0) {
        return;
    }

    // loop through conditions
    for (let i = 0; i < conditions.length; i++) {

        // current condition
        const conditionData = conditions[i];

        // create new condition
        createdConditionData = this.newCondition();
        const typesDiv = createdConditionData.types;
        const contentDiv = createdConditionData.content;

        // types choice
        const typeSelectList = this.getChildByClassName(typesDiv, selectListClass);
        typeSelectList.value = conditionData.type
        this.onTypeChange(typeSelectList);

        // check type, incl type, min stock
        if (includeTypes.includes(conditionData.type)) {
            const inclTypeDiv = this.getChildByClassName(contentDiv, inclExclTypesClass);
            const inclTypeSelectList = this.getChildByClassName(inclTypeDiv, selectListClass);
            inclTypeSelectList.value = conditionData.include_type;
        } else if (conditionData.type === 'stock') {
            const minStockDiv = this.getChildByClassName(contentDiv, minStockClass);
            const minStockInput = this.getChildByClassName(minStockDiv, 'numberinput');
            minStockInput.value = conditionData.min_stock;
        }

        // check field
        const fld = conditionData.field;
        if (fld === null || fld === 'null') {
            continue;
        }


        const fieldDiv = this.getChildByClassName(contentDiv, 'fields');
        const fieldSelectList = this.getChildByClassName(fieldDiv, selectListClass);
        fieldSelectList.value = fld;
        this.onFieldChange(fieldSelectList);

        // populate content by field
        const fldContent = this.getChildByClassName(fieldDiv, fieldContentClass);

        // wh, cat, brand
        if (fldSelectTypes.includes(fld)) {
            const valuesSelectDiv = this.getChildByClassName(fldContent, fldSelectListClasses[fld]);
            const valuesSelectList = this.getChildByClassName(valuesSelectDiv, multiselectListClass);
            this.markSelectList(valuesSelectList, conditionData.values);

            // custom ui for the good
        } else if (fld === 'good') {
            const savedGoodsDiv = this.getChildByClassName(fldContent, savedGoodsDivClass);
            const savedGoodsList = this.getChildByClassName(savedGoodsDiv, savedGoodsListClass);
            const goods = this.getGoodsBySku(conditionData.values);
            this.appendToUL(savedGoodsList, goods);
            this.setSavedGoodsHeaderByGoodsList(savedGoodsList);
        }
    }
}

UI.collectConditions = function () {
    const conditionsTextArea = document.getElementById('id_content');
    const conditions = [];
    const conditionsDiv = this.getConditionsDiv();

    for (let i = 0; i < conditionsDiv.children.length; i++) {

        //current condition div
        const conditionDiv = conditionsDiv.children[i];

        // put current condition content into this object
        const conditionData = {
            type: null,
            field: null,
            values: [],
            include_type: null,
            min_stock: null,
        }

        let conditionType = this.getConditionCurrentType(conditionDiv);
        if (conditionType === 'null') {
            conditionType = null;
        }
        conditionData.type = conditionType;

        // condition type not selected
        if (conditionType === null) {
            conditions.push(conditionData);
            continue;
        }

        // get condition content
        const content = this.getChildByClassName(conditionDiv, conditionContentClass);
        if (content == null) {
            conditions.push(conditionData);
            continue;
        }

        // check incl type
        if (includeTypes.includes(conditionType)) {

            //get incl type div
            const inclTypeDiv = this.getChildByClassName(content, inclExclTypesClass);
            if (inclTypeDiv === null) {
                conditions.push(conditionData);
                continue;
            }

            const inclTypeSelectList = this.getChildByClassName(inclTypeDiv, selectListClass);
            if (inclTypeSelectList === null) {
                conditions.push(conditionData);
                continue;
            }
            conditionData.include_type = inclTypeSelectList.value;

        } else if (conditionType === 'stock') {

            // get min stock div
            const minStockDiv = this.getChildByClassName(content, minStockClass);
            if (minStockDiv === null) {
                conditions.push(conditionData);
                continue;
            }
            const minStockInput = this.getChildByClassName(minStockDiv, 'numberinput');
            conditionData.min_stock = minStockInput.value;
        }

        // check field
        const fldDiv = this.getChildByClassName(content, 'fields');
        if (fldDiv === null) {
            conditions.push(conditionData);
            continue;
        }

        const fldSelectList = this.getChildByClassName(fldDiv, selectListClass);
        if (fldSelectList === null) {
            conditions.push(conditionData);
            continue;
        }

        const fld = fldSelectList.value;
        conditionData.field = fld;

        // get selected values' ids
        const fldContentDiv = this.getChildByClassName(fldDiv, fieldContentClass);
        if (fldContentDiv === null) {
            conditions.push(conditionData);
            continue;
        }

        // warehouse, cat or brand
        if (fldSelectTypes.includes(fld)) {
            // get select list div
            className = fldSelectListClasses[fld];
            selectListDiv = this.getChildByClassName(fldContentDiv, className);

            // wanted div not found for some reason
            if (selectListDiv === null) {
                conditions.push(conditionData);
                continue;
            }

            const fldSelectList = this.getChildByClassName(selectListDiv, multiselectListClass);
            if (fldSelectList === null) {
                conditions.push(conditionData);
                continue;
            }

            const values = this.getValuesFromSelectList(fldSelectList);
            conditionData.values = [].concat(values);

        } else if (fld === 'good') {

            // get saved goods div
            const savedGoodsDiv = this.getChildByClassName(fldContentDiv, savedGoodsDivClass);
            if (savedGoodsDiv === null) {
                conditions.push(conditionData);
                continue;
            }

            // get saved goods list
            const savedGoodsList = this.getChildByClassName(savedGoodsDiv, savedGoodsListClass);
            if (savedGoodsList === null) {
                conditions.push(conditionData);
                continue;
            }

            const values = this.getValuesFromUL(savedGoodsList);
            conditionData.values = [].concat(values);
        }

        conditions.push(conditionData);
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
    return {
        condition: condition,
        types: types,
        content: content,
    };
}

UI.selectOptions = function (list, selected) {
    for (let i = 0; i < list.options.length; i++) {
        let option = list.options[i];
        option.selected = selected;
    }
}

UI.getChildByClassName = function (parent, childClassName) {
    const children = parent.children;
    for (let i = 0; i < children.length; i++) {
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

    // this is the goods searh results tool bar cmd
    if (selected && cmd.classList.contains(goodsSearchResultsToolbarCmdClass)) {
        this.onSelectSearchResult(selectList);
    }
}

UI.getContentDiv = function (conditionDiv) {
    const wantedClass = conditionContentClass;
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
            `number-input ${minStockClass}`,
            'Остаток по полю условия больше или равен',
            'onkeyup',
            'validateNumberInputMinValue(this, 1);',
            1,
        );
        conditionContentDiv.appendChild(stockInput);
    }

    const fieldsList = this.newFieldsList();
    conditionContentDiv.appendChild(fieldsList);
}

UI.newInclExclTypesList = function () {
    const container = document.createElement('div');
    container.className = `form-group ${inclExclTypesClass}`;

    label = document.createElement('label');
    label.appendChild(document.createTextNode('Остаток по полю условия'));
    container.appendChild(label);

    const types = this.getInclExclTypes();
    const select = this.newOptionList(types);
    container.appendChild(select);
    return container;
}

UI.newInput = function (type, className, labelStr, eventName, eventHandler, minValue) {
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
    if (minValue !== null) {
        input.setAttribute('min', minValue);
    }

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
                if (innerChild.classList.contains(selectListClass)) {
                    return innerChild.value;
                }
            }
        }
    }
}


UI.newOptionList = function (src) {
    const selectList = document.createElement('select');
    selectList.className = `csvselect form-control ${selectListClass}`;
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

        const savedGoodsBox = this.newUL(savedGoodsDivClass, savedGoodsHeader, [], true);
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

UI.setSavedGoodsHeaderByGoodsList = function (list) {
    const searchResultsBox = list.previousSibling;
    const searchResultsLabel = this.getChildByClassName(searchResultsBox, toolbarLabel);
    this.setSavedGoodsHeader(searchResultsLabel, list.children.length);
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

    let input = clearSpaces(el.value.toLowerCase());
    if (input.length < minGoodsSearchInputLength) {
        resultsList.size = 1;
        this.setSearchResultsHeaderText(label, 0);
        return;
    }

    const items = Storage.get('goods');
    let matched = 0;

    items.forEach(function (item) {
        
        if (clearSpaces(item.name.toLowerCase()).includes(input)
            || clearSpaces(item.sku.toLowerCase()).includes(input)) {
            
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

function clearSpaces(src) {
    const result = src.replace(/\s+/g, '');
    return result;
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
    fieldContent.className = `form-group ${fieldContentClass}`;
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
    selectAll.className = 'toolbar-cmd text-muted';

    // custom class for goods' search results select list  
    if (className === 'goods') {
        selectAll.classList.add(goodsSearchResultsToolbarCmdClass);
    }

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

UI.getValuesFromSelectList = function (list) {
    const vals = [];
    for (let i = 0; i < list.options.length; i++) {
        const option = list.options[i];
        if (option.selected) {
            vals.push(option.value);
        }
    }
    return vals;
}

UI.markSelectList = function (list, vals) {
    for (let i = 0; i < list.options.length; i++) {
        const option = list.options[i];
        if (vals.includes(option.value)) {
            option.selected = true;
        }
    }
}

UI.getGoodsBySku = function (skus) {
    items = [];
    goods = Storage.get('goods');
    goods.forEach(function (good) {
        if (skus.includes(good.sku)) {
            const item = {
                val: good.sku,
                text: good.name,
            }
            items.push(item);
        }
    });
    return items;
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

function isJSON(str) {
    try {
        return (JSON.parse(str) && !!str);
    } catch (e) {
        return false;
    }
}

function getGoodsViaApi(url) {
    Api.get(getGoodsApiUrl);
}

function init() {
    // UI.hideConditionsTextArea();
    getGoodsViaApi();
    UI.buildConditions();
    scrollToTop();
}

document.addEventListener("DOMContentLoaded", init());

