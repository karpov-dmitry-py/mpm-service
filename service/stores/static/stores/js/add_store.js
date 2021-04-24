const marketplace_select = document.querySelector('#id_marketplace');
marketplace_select.addEventListener('input', onSelectMarketplace);

function onSelectMarketplace(e) {
    const settings_div = document.querySelector('#settings-placeholder');
    settings_div.innerHTML = '';
    let selected_value = e.target.selectedOptions[0].value;
    if (selected_value === '') {
        return true;
    }
    selected_value = e.target.selectedOptions[0].text;
    const marketplace_blocks = document.querySelectorAll('.marketplace-block');
    for (i = 0; i < marketplace_blocks.length; i++) {
        let node = marketplace_blocks[i];
        if (node.id === selected_value) {
            settings_div.innerHTML = node.innerHTML;
            break;
        }
    };
}
