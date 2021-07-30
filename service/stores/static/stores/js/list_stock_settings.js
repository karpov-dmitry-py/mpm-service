document.addEventListener("DOMContentLoaded", init());

function init() {
    styleSettings();
    hideElById('div_id_selected_settings');
}

function hideElById(id) {
    const el = document.getElementById(id);
    if (el === null) {
        return;
    }
    el.style.display = 'none';
}

function styleSettings () {
    const settingNotUsedText = document.querySelector('.setting-not-used-text').innerText.trim();
    const rows = document.querySelectorAll('.setting_row');
    rows.forEach(function(row) {
        const stockTd = getChildByClassName(row, 'setting_stock');
        if (stockTd.innerText === settingNotUsedText) {
            row.classList.add('inactive');
        }
    });
}

function getChildByClassName (parent, childClassName) {
    const children = parent.children;
    for (let i = 0; i < children.length; i++) {
        let child = children[i];
        if (child.classList.contains(childClassName)) {
            return child;
        }
    }
}

const mainCheckbox = document.getElementById('main-checkbox');
mainCheckbox.onchange = toggleCheckboxes;

function toggleCheckboxes(e) {
    const checkBoxes = document.querySelectorAll('.item-checkbox');
    checkBoxes.forEach( function (item) {
        item.checked = e.target.checked;
    });
}

function updateGoodProperty(e) {
    const checkBoxes = document.querySelectorAll('.item-checkbox');
    let checkedItems = [];
    checkBoxes.forEach( function (item) {
        if (item.checked) {
            checkedItems.push(item.value);
        }
    });
    const result = JSON.stringify(checkedItems);
    const checkedSettings = document.createElement('input');
    checkedSettings.style.display = 'none';
    checkedSettings.id = 'checked-settings';
    checkedSettings.name = 'checked-settings';
    checkedSettings.value = result;
    const form_id = `#${e.target.name}`
    const form = document.querySelector(form_id);
    form.appendChild(checkedSettings);
}

function checkPriority(numberInput) {
    console.log(numberInput.value);
    if (numberInput.value < 1) {
        numberInput.value = 1;
    }
    console.log(numberInput.value);
}

function getSelectedSettings () {
    collectSelectedSettings ('item-checkbox', 'id_selected_settings');
}

function collectSelectedSettings (srcClass, dstID) {
    srcClass = `.${srcClass}`;
    const items = document.querySelectorAll(srcClass);
    let selected = [];
    items.forEach(function(item) {
        if (item.checked === true) {
            selected.push(item.value);
        }
    });
    dstID = `#${dstID}`;
    const formFld = document.querySelector(dstID);
    formFld.value = selected.join(',');
}