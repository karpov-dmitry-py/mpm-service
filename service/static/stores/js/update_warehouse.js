function getSupplierWarehouseType () {
    return 'Склад поставщика';
}

function handleSubmit(e) {
    typeDropdown.style.display = 'none';
    typeDropdown.disabled = false;
}

const btnSubmit = document.getElementById('btn-submit');
btnSubmit.addEventListener('click', handleSubmit);

const supplierDropdown = document.getElementById('id_supplier');
const typeDropdown = document.getElementById('id_kind');
typeDropdown.disabled = true;

if (typeDropdown.selectedOptions[0].textContent !== getSupplierWarehouseType()) {
    supplierDropdown.disabled = true;
}




