document.addEventListener("DOMContentLoaded", init());

function init() {
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

// const btnUpdateBrand = document.querySelector('.batch-update-brand');
// btnUpdateBrand.addEventListener('click', updateGoodProperty);

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