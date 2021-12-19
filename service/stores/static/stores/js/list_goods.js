const mainCheckbox = document.getElementById('main-checkbox');
mainCheckbox.onchange = toggleCheckboxes;

const btnUpdateBrand = document.querySelector('.batch-update-brand');
btnUpdateBrand.addEventListener('click', updateGoodProperty);

const btnUpdateCategory = document.querySelector('.batch-update-category');
btnUpdateCategory.addEventListener('click', updateGoodProperty);

const btnBatchDelete = document.querySelector('.batch-delete-goods');
btnBatchDelete.addEventListener('click', updateGoodProperty);

const btnApplyFilters = document.querySelector('#apply-filters');
btnApplyFilters.addEventListener('click', collectFilters);

const btnFilterAll = document.querySelector('.filter-all-btn');
btnFilterAll.addEventListener('click', toggleFilterAll);

function updateGoodProperty(e) {
    const checkBoxes = document.querySelectorAll('.item-checkbox');
    let checkedItems = [];
    checkBoxes.forEach( function (item) {
        if (item.checked) {
            checkedItems.push(item.value);
        }
    });
    const result = JSON.stringify(checkedItems);
    const checkedGoodsList = document.createElement('input');
    checkedGoodsList.style.display = 'none';
    checkedGoodsList.id = 'checked-goods-list';
    checkedGoodsList.name = 'checked-goods-list';
    checkedGoodsList.value = result;
    const form_id = `#${e.target.name}`
    const form = document.querySelector(form_id);
    form.appendChild(checkedGoodsList);
}

function toggleCheckboxes(e) {
    toggleCheckboxesWithVal(e.target.checked, false);
}

function toggleCheckboxesWithVal(is_checked, setDisabled) {
    const checkBoxes = document.querySelectorAll('.item-checkbox');
    checkBoxes.forEach( function (item) {
        item.checked = is_checked;
        if (setDisabled) {
            item.disabled = is_checked;
        }
    });
}

// build category select list
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

function prepareCategoryBatchUpdateList() {
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

function getBrandsFilterItem(id, name, checked) {
    const isChecked = checked===true ? "checked" : "";
    const src = `
    <li class="list-group-item" style="background-color: #F0F8FF; margin-left:0px; padding-top: 3px; padding-bottom: 3px;">
        <input type="checkbox" ${isChecked} value=${id} class="form-check-input brand-filter-value" id="brand_${id}">
        <label class="form-check-label" for="brand_${id}">
        ${name}
        </label>
    </li>
    `
    return src;
}


function setCategoriesFilterList() {
    const categoryFilterList = document.querySelector('#category-filter-list');
    const categoriesList = document.querySelector('#categories_filter_source');
    items = JSON.parse(categoriesList.innerText);

    const urlParams = new URLSearchParams(window.location.search);
    let checkedCategories = urlParams.get('cats');
    if (checkedCategories === null) {
        checkedCategories = [];
    } else {
        checkedCategories = checkedCategories.split(',');
    }

    sourceObj = {
        str: '',
        level: 0,
        checked: checkedCategories,
    }
    build_category_filter_list(items, sourceObj);
    categoryFilterList.innerHTML = sourceObj.str;
    categoriesList.remove();
}


function build_category_filter_list(items, sourceObj) {
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
        
        if (item.id === 'empty') {
            item.id = "null";
        }
        let isChecked = '';
        sourceObj.checked.forEach(function (checkedID) {
            if (item.id == checkedID) {
                isChecked = 'checked';            
            }
        });
        const src = `
        <li class="list-group-item" style="background-color: #F0F8FF; margin-left:0px; padding-top: 3px; padding-bottom: 3px;">
        <input type="checkbox" ${isChecked} value=${item.id} class="form-check-input category-filter-value" id="category_${item.id}">
            <label class="form-check-label" for="category_${item.id}">
            ${label}
            </label>
        </li>
        `
        sourceObj.str += src;
        if ('childs' in item) {
            sourceObj.level += 1;
            build_category_filter_list(item.childs, sourceObj)
            sourceObj.level -= 1;
        }
    });
}

function setBrandsFilterList() {
    const brandsSource = document.querySelector('#brands_filter_source');
    const brands = JSON.parse(brandsSource.innerText);
    let src = '';
    brands.forEach(function (item) {
        src += getBrandsFilterItem(item.id, item.name, item.checked);
    });
    const brandsFilterList = document.querySelector('#brand-filter-list');
    brandsFilterList.innerHTML = src;
    brandsSource.remove();
}

function setFilters() {
    setBrandsFilterList();
    setCategoriesFilterList();
}

function onLoad(e) {
    setFilters();
    prepareCategoryBatchUpdateList();
    setQueryParams();
}

function collectFiltersByType (sourceClass, destinationID) {
    sourceClass = `.${sourceClass}`;
    const items = document.querySelectorAll(sourceClass);
    let filters = [];
    items.forEach(function(item) {
        if (item.checked === true) {
            filters.push(item.value);
        }
    });
    destinationID = `#${destinationID}`;
    const filtersFormFld = document.querySelector(destinationID);
    filtersFormFld.value = filters;
}

function collectFilters(e) {
    // e.preventDefault();
    collectFiltersByType('brand-filter-value', 'brands');
    collectFiltersByType('category-filter-value', 'cats');
}


function toggleFilterAll(e) {
    const filtersAllInputs = document.querySelectorAll('.filter-all-val');
    let val = false;
    filtersAllInputs.forEach(function (item) {
        val = !item.checked;   
        item.checked = val;
        item.value = val;
    });

    const sep = ':';
    const btn = e.target;
    const goodsCount = btn.innerText.split(sep)[1];
    const labels = {
        true: 'Снять выделение. Выбрано товаров',
        false: 'Выбрать все товары',
    }
  
    const btnStyles = {
        true: 'btn-info',
        false: 'btn-light',
    }

    btn.innerText = `${labels[val]}${sep} ${goodsCount}`;
    btn.classList.remove(btnStyles[!val]);
    btn.classList.add(btnStyles[val]);

    toggleCheckboxesWithVal(val, true);
    mainCheckbox.checked = val;
    mainCheckbox.disabled = val;
}

function getQueryParams() {
    return new URLSearchParams(window.location.search);
}


function setQueryParams() {
    const params = getQueryParams();
    payload = {
        brands: params.get('brands'),
        cats: params.get('cats'),
    }
    json = JSON.stringify(payload);
    const receivers = document.querySelectorAll('.query-params');
    receivers.forEach(function(item) {
        item.value = json;
    });
}