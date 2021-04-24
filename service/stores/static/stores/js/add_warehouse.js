const supplierDropdown = document.getElementById('id_supplier');
const typeDropdown = document.getElementById('id_kind');
if (typeDropdown.selectedOptions[0].textContent !== getSupplierWarehouseType()) {
    supplierDropdown.disabled = true;
}

function getSupplierWarehouseType () {
    return 'Склад поставщика';
}

function checkType(element) {
    if (element.selectedOptions[0].textContent === getSupplierWarehouseType()) {
        supplierDropdown.disabled = false;
    } else {
        supplierDropdown.value = '';
        supplierDropdown.disabled = true;
    }
}