const fs = require('fs');
const path = require('path');

const views = path.resolve(
    __dirname,
    '..',
    'src',
    'opnsense',
    'mvc',
    'app',
    'views',
    'OPNsense',
    'DeviceMonitor'
);

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

function readView(name) {
    return fs.readFileSync(path.join(views, name), 'utf8');
}

const cases = [
    { file: 'devices.volt', id: 'filter-status', style: 'btn-default btn-sm' },
    { file: 'infrastructureservices.volt', id: 'services-type-filter', style: 'btn-default btn-sm' },
    { file: 'infrastructureservices.volt', id: 'services-status-filter', style: 'btn-default btn-sm' },
    { file: 'identityevents.volt', id: 'identity-events-status', style: 'btn-default btn-xs' },
    { file: 'identityevents.volt', id: 'identity-events-limit', style: 'btn-default btn-xs' },
    { file: 'scanhistory.volt', id: 'scan-history-limit', style: 'btn-default btn-xs' }
];

cases.forEach(function(spec) {
    const text = readView(spec.file);
    const match = text.match(
        new RegExp('<select[^>]*id="' + spec.id + '"[^>]*>')
    );

    check(
        match !== null,
        spec.file + ' #' + spec.id + ' <select> not found'
    );

    const select = match[0];

    check(
        select.includes('class="selectpicker"'),
        spec.file + ' #' + spec.id + ' is missing class="selectpicker"'
    );

    check(
        select.includes('data-style="' + spec.style + '"'),
        spec.file + ' #' + spec.id +
            ' is missing data-style="' + spec.style + '"'
    );

    check(
        !select.includes('form-control') && !select.includes('input-sm'),
        spec.file + ' #' + spec.id +
            ' still uses native form-control/input-sm classes'
    );
});

// Port Discovery now uses a searchable per-device table in place of a select.
const infrastructure = readView('infrastructureservices.volt');
check(infrastructure.includes('id="port-discovery-search"'),
    'Port Discovery search is missing');
check(infrastructure.includes('id="port-discovery-devices"'),
    'Port Discovery device table is missing');
check(infrastructure.includes('id="btn-port-discovery-save"'),
    'Port Discovery bulk save is missing');

// #services-type-filter options are appended asynchronously by populateTypes(),
// so the view must refresh the selectpicker after appending them.
check(
    readView('infrastructureservices.volt').includes(
        "$select.selectpicker('refresh');"
    ),
    'infrastructureservices.volt #services-type-filter does not refresh ' +
        'selectpicker after populating options'
);

console.log('DEVICE_SELECTPICKER_STATIC=PASS');
