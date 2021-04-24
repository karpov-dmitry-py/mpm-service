document.addEventListener('DOMContentLoaded', onLoad);

function onLoad(e) {
    const categories_block = document.querySelector('#categories_json');
    const _json = categories_block.innerHTML;
    const sourceObj = {
        source: '<div class="list-group list-group-root well">',
        marginLeft: 0,
        level: 1,
    };
    const items = JSON.parse(_json);
    items.forEach( function(item) {
        processItem(item, sourceObj);
    });
    sourceObj.source += '</div>';
    categories_block.innerHTML = sourceObj.source;
    categories_block.style.display = 'block';
}

function getStyleAsString(obj) {
    return `style="margin-left: ${obj.marginLeft}px; padding-left: 0px;"`;
}

function processItem(item, sourceObj) {
    const leftMarginStep = 35;
    let childs_count;
    if (item.childs_count > 0) {
        childs_count = ` (${item.childs_count})`;
    } else {
        childs_count = '';
    }
    const currentItem = `${item.name}${childs_count}`;
    const item_id = 'block-' + item.id;
    const href_item_id = `#${item_id}`;

    sourceObj.marginLeft = leftMarginStep;
    let style = getStyleAsString(sourceObj);
    const tag = `<div class="row align-items-center"><div class="col-10"><a href=${href_item_id} ${style} class="list-group-item list-group-item-action" data-toggle="collapse">
                    ${currentItem}</a></div><div class="col-2"><span class="pull-right"><a class="cat-icon" href="/categories/${item.id}/update"><i class="fa fa-edit"></i></a><a class="cat-icon" style="margin-left: 0.5rem;" href="/categories/${item.id}/delete"><i class="fa fa-trash-alt"></i></a></span></div></div>`;
    sourceObj.source += tag;
    if ('childs' in item) {
        sourceObj.level += 1;
        style = getStyleAsString(sourceObj);
        sourceObj.source += `<div ${style} class="list-group list-group-root expanded" id=${item_id}>`;
        item.childs.forEach( function(child) {
            processItem(child, sourceObj);
        });
        sourceObj.source += '</div>';
        sourceObj.level -= 1;
    }
}