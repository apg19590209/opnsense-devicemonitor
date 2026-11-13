const fs = require('fs');
const vm = require('vm');

const devicesPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt';
const settingsPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt';

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

/* Extract one JavaScript function by balancing braces. Stopping at the next
 * `function` token would truncate a loader at its nested AJAX callbacks. */
function extractFunction(source, name) {
    const start = source.indexOf('function ' + name);
    check(start !== -1, name + ' missing');

    const open = source.indexOf('{', start);
    check(open !== -1, name + ' has no body');

    let depth = 0;
    let quote = '';
    let escaped = false;

    for (let i = open; i < source.length; i += 1) {
        const ch = source[i];

        if (quote) {
            if (escaped) {
                escaped = false;
            } else if (ch === '\\') {
                escaped = true;
            } else if (ch === quote) {
                quote = '';
            }
            continue;
        }

        if (ch === "'" || ch === '"' || ch === '`') {
            quote = ch;
            continue;
        }

        if (ch === '{') {
            depth += 1;
        } else if (ch === '}') {
            depth -= 1;
            if (depth === 0) {
                return source.slice(start, i + 1);
            }
        }
    }

    check(false, name + ' has an unterminated body');
}

function loadFunction(viewPath, name, globals) {
    const source = fs.readFileSync(viewPath, 'utf8');
    const snippet = extractFunction(source, name);
    const sandbox = Object.assign({}, globals || {});
    vm.runInNewContext(
        snippet + '\nthis.loadedFunction = ' + name + ';',
        sandbox
    );
    return sandbox.loadedFunction;
}

const devicesModel = loadFunction(devicesPath, 'buildHaNoticeModel');
const settingsModel = loadFunction(settingsPath, 'buildHaNoticeModel');

const t = {
    unknown: 'UNKNOWN',
    unavailable: 'UNAVAILABLE',
    non_ha: 'NON_HA',
    unconfirmed: 'UNCONFIRMED',
    ha_status_unconfirmed: 'HA_STATUS_UNCONFIRMED',
    detected_role: 'DETECTED_ROLE',
    effective_mode: 'EFFECTIVE_MODE',
    monitoring: 'MONITORING',
    enabled: 'ENABLED',
    disabled: 'DISABLED',
    monitoring_enabled: 'MONITORING_ENABLED',
    monitoring_disabled: 'MONITORING_DISABLED',
    monitoring_status_unknown: 'MONITORING_STATUS_UNKNOWN',
    some_activities_paused: 'SOME_ACTIVITIES_PAUSED',
    paused_activities: 'PAUSED_ACTIVITIES',
    continuing_activities: 'CONTINUING_ACTIVITIES',
    show_details: 'SHOW_DETAILS',
    hide_details: 'HIDE_DETAILS',
    ha_paused_activities: 'HA_PAUSED_ACTIVITIES',
    monitoring_disabled_note: 'MONITORING_DISABLED_NOTE',
    role_mode_difference: 'ROLE_MODE_DIFFERENCE',
    role_override_active: 'ROLE_OVERRIDE_ACTIVE',
    node_local: 'NODE_LOCAL',
    ownership: 'OWNERSHIP',
    no_paused: 'NO_PAUSED',
    paused_heading: 'PAUSED_HEADING',
    visibility_priming: 'ACT_VISIBILITY',
    service_discovery: 'ACT_DISCOVERY',
    service_alerts: 'ACT_SERVICE_ALERTS',
    identity_alerts: 'ACT_IDENTITY_ALERTS',
    new_device_alerts: 'ACT_NEW_DEVICE_ALERTS',
    targeted_nmap: 'ACT_AUTOMATIC_TARGETED_NMAP',
    continuation: 'CONTINUATION',
    paused_note: 'PAUSED_NOTE',
    role_unavailable: 'ROLE_UNAVAILABLE',
    fetch_failed: 'FETCH_FAILED',
    role_unknown_observation_continues: 'OBSERVATION_CONTINUES',
    carp_aware_off: 'AWARENESS_OFF',
    role_check_failed: 'ROLE_CHECK_FAILED',
    non_ha_unconfirmed_no_interfaces: 'NO_MONITORED_INTERFACES',
    non_ha_unconfirmed_carp_no_interfaces: 'CARP_PRESENT_NO_MONITORED_INTERFACES',
    non_ha_unconfirmed_unresolved_interfaces: 'UNRESOLVED_MONITORED_INTERFACES',
    non_ha_unconfirmed_carp_vip: 'CARP_VIP_CONFIGURED',
    non_ha_unconfirmed_generic: 'HA_STATUS_UNCONFIRMED_GENERIC',
    last_scan: 'LAST_SCAN',
    timezone_unavailable: 'TIMEZONE_UNAVAILABLE',
    no_scan: 'NO_SCAN',
    scan_unavailable: 'SCAN_UNAVAILABLE',
    scan_fetch_failed: 'SCAN_FETCH_FAILED',
    status_permitted: 'PERMITTED',
    status_paused_by_ha: 'PAUSED_BY_HA'
};

const paused = [
    'visibility_priming',
    'service_discovery',
    'service_alerts',
    'identity_alerts',
    'new_device_alerts',
    'targeted_nmap'
];

const previewT = {
    unknown: 'unknown',
    unavailable: 'Unavailable',
    non_ha: 'Non-HA',
    unconfirmed: 'Unconfirmed',
    ha_status_unconfirmed: 'HA status unconfirmed',
    detected_role: 'Detected role',
    effective_mode: 'Effective mode',
    monitoring: 'Monitoring',
    enabled: 'Enabled',
    disabled: 'Disabled',
    monitoring_enabled: 'Monitoring enabled',
    monitoring_disabled: 'Monitoring disabled',
    monitoring_status_unknown: 'Monitoring status unknown',
    some_activities_paused: 'Some activities paused',
    paused_activities: 'Paused activities',
    continuing_activities: 'Continuing activities',
    show_details: 'Show details',
    hide_details: 'Hide details',
    ha_paused_activities: 'HA-paused activities',
    monitoring_disabled_note: 'Monitoring is disabled; scheduled scans and alert evaluation are not running.',
    role_mode_difference: 'Detected and effective roles differ.',
    role_override_active: 'Role override is active.',
    node_local: 'Node-local Device Monitor data',
    ownership: 'Displayed data belongs to this node only and is not merged from the CARP peer.',
    no_paused: 'No Device Monitor activities are paused by HA gating.',
    paused_heading: 'Paused on this BACKUP node',
    visibility_priming: 'Visibility priming',
    service_discovery: 'Service discovery',
    service_alerts: 'Service alerts',
    identity_alerts: 'Identity conflict alerts',
    new_device_alerts: 'New device alerts',
    targeted_nmap: 'Automatic targeted Nmap scans',
    continuation: 'Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.',
    paused_note: 'A paused activity is not an empty result.',
    role_unavailable: 'HA role status is unavailable. Confirm CARP and the effective mode before relying on this view.',
    fetch_failed: 'HA status could not be retrieved, so the current CARP gating state is unknown.',
    role_unknown_observation_continues: 'Device Monitor reports that observation continues while the CARP role is unknown.',
    carp_aware_off: 'CARP awareness is disabled, so no activities are paused.',
    role_check_failed: 'The detected CARP role is unavailable; the effective mode comes from the role override.',
    non_ha_unconfirmed_no_interfaces: 'HA status is unconfirmed because no monitored interface is selected.',
    non_ha_unconfirmed_carp_no_interfaces: 'HA status is unconfirmed because CARP is configured or active on this appliance, but no monitored interface is selected; monitoring-scope roles are unknown.',
    non_ha_unconfirmed_unresolved_interfaces: 'HA status is unconfirmed because the selected monitored interfaces do not resolve to local devices.',
    non_ha_unconfirmed_carp_vip: 'HA status is unconfirmed because CARP virtual IPs are configured without a detected CARP role.',
    non_ha_unconfirmed_generic: 'HA status is unconfirmed. Confirm CARP and the selected monitored interfaces.',
    last_scan: 'Last successful local scan',
    timezone_unavailable: 'Timezone unavailable',
    no_scan: 'No successful local scan appears in the available scan history.',
    scan_unavailable: 'The local scan history could not be read.',
    scan_fetch_failed: 'Scan history was not retrieved because the HA status request failed.'
};

function fixture(overrides) {
    return Object.assign({
        role: 'none',
        mode: 'none',
        role_available: true,
        config_available: true,
        role_mixed: false,
        carp_aware: true,
        observing: true,
        paused_activities: [],
        role_unknown_observation_continues: false,
        monitoring_enabled: true,
        override: 'auto',
        override_active: false,
        non_ha_confirmed: false,
        ha_relevant: true,
        node: 'dm-node.test',
        last_scan: '2026-11-13 08:25:16',
        last_scan_state: 'found',
        last_scan_timezone: 'Australia/Sydney'
    }, overrides);
}

const cases = {
    master: {
        data: fixture({ha_status: 'master', role: 'MASTER', mode: 'MASTER'}),
        expect: function (m) {
            check(m.role === 'MASTER', 'MASTER detected role');
            check(m.mode === 'MASTER', 'MASTER effective mode');
            check(m.paused.length === 0, 'MASTER must not list paused activities');
            check(m.tone === 'info', 'MASTER tone');
            check(m.lastScan === 'LAST_SCAN: 2026-11-13 08:25:16 (Australia/Sydney)',
                'MASTER last successful scan with verified timezone');
            check(m.monitoringEnabled === true, 'MASTER monitoring-enabled state');
            check(m.monitoringLabel === 'ENABLED', 'MASTER monitoring label');
            check(m.summary === 'dm-node.test \u00b7 MASTER \u00b7 MONITORING_ENABLED',
                'MASTER summary must be one compact fact line');
            check(m.summaryWarning === '', 'MASTER must not show a warning');
            check(m.activityRelevant === true, 'MASTER activity details missing');
            check(m.pausedHeading === 'PAUSED_ACTIVITIES', 'paused heading');
            check(m.continuingHeading === 'CONTINUING_ACTIVITIES', 'continuing heading');
        }
    },
    monitoring_disabled_master: {
        data: fixture({
            ha_status: 'master', role: 'MASTER', mode: 'MASTER',
            monitoring_enabled: false
        }),
        expect: function (m) {
            check(m.monitoringEnabled === false, 'disabled monitoring state');
            check(m.monitoringLabel === 'DISABLED', 'disabled monitoring label');
            check(m.summary === 'dm-node.test \u00b7 MASTER \u00b7 MONITORING_DISABLED',
                'summary must show monitoring disabled once');
            check(m.summary.indexOf('HA_PAUSED_ACTIVITIES') === -1,
                'disabled monitoring must not invent HA pauses');
            check(m.monitoringNote === undefined,
                'expanded area repeats the monitoring status');
        }
    },
    monitoring_disabled_backup: {
        data: fixture({
            ha_status: 'backup', role: 'BACKUP', mode: 'BACKUP',
            observing: false, paused_activities: paused,
            monitoring_enabled: false
        }),
        expect: function (m) {
            check(m.summary.indexOf('MONITORING_DISABLED') !== -1,
                'disabled BACKUP must show monitoring disabled');
            check(m.summary.indexOf('SOME_ACTIVITIES_PAUSED') !== -1,
                'disabled BACKUP must show the compact paused indicator');
            check(m.paused.length === 6,
                'disabled BACKUP must retain the exact paused list');
        }
    },
    role_difference: {
        data: fixture({
            ha_status: 'backup', role: 'MASTER', mode: 'BACKUP',
            observing: false, paused_activities: paused
        }),
        expect: function (m) {
            check(m.roleDiffers === true, 'role difference not detected');
            check(m.summaryWarning.indexOf('ROLE_MODE_DIFFERENCE') !== -1,
                'role difference warning missing');
            check(m.summaryWarning.indexOf('DETECTED_ROLE') === -1 &&
                m.summaryWarning.indexOf('EFFECTIVE_MODE') === -1,
                'collapsed warning must not repeat the expanded role facts');
        }
    },
    backup: {
        data: fixture({
            ha_status: 'backup', role: 'BACKUP', mode: 'BACKUP',
            observing: false, paused_activities: paused
        }),
        expect: function (m) {
            check(m.role === 'BACKUP', 'BACKUP detected role');
            check(m.mode === 'BACKUP', 'BACKUP effective mode');
            check(m.tone === 'warning', 'BACKUP tone');
            check(JSON.stringify(m.paused) === JSON.stringify([
                'ACT_VISIBILITY',
                'ACT_DISCOVERY',
                'ACT_SERVICE_ALERTS',
                'ACT_IDENTITY_ALERTS',
                'ACT_NEW_DEVICE_ALERTS',
                'ACT_AUTOMATIC_TARGETED_NMAP'
            ]), 'BACKUP paused activity list');
            check(m.continuation === 'CONTINUATION', 'BACKUP continuation wording');
            check(m.pausedNote === 'PAUSED_NOTE', 'BACKUP empty-result distinction');
            check(m.summary === 'dm-node.test \u00b7 BACKUP \u00b7 MONITORING_ENABLED \u00b7 SOME_ACTIVITIES_PAUSED',
                'BACKUP summary must retain a short paused indicator');
            check(m.summaryWarning === '', 'BACKUP must not show a warning');
        }
    },
    non_ha: {
        data: fixture({
            ha_status: 'non_ha', override: 'auto', override_active: false,
            non_ha_confirmed: true, ha_relevant: false
        }),
        expect: function (m) {
            check(m.haRelevant === false, 'confirmed non-HA must hide HA-specific content');
            check(m.nonHaConfirmed === true, 'confirmed non-HA flag lost');
            check(m.overrideActive === false, 'non-HA auto state marked override active');
            check(m.role === 'NON_HA', 'non-HA detected role label');
            check(m.mode === 'NON_HA', 'non-HA effective mode label');
            check(m.paused.length === 0, 'non-HA must not pause activities');
            check(m.summary === 'dm-node.test \u00b7 MONITORING_ENABLED',
                'confirmed non-HA must omit the HA role from the compact line');
            check(m.activityRelevant === false,
                'confirmed non-HA must not show HA activity details');
            check(m.lastScan === 'LAST_SCAN: 2026-11-13 08:25:16 (Australia/Sydney)',
                'non-HA must retain last successful scan and timezone');
            check(m.ownership === 'NODE_LOCAL',
                'confirmed non-HA must retain node-local wording without CARP-peer wording');
            check(m.monitoringLabel === 'ENABLED', 'non-HA must retain monitoring state');
            check(m.node === 'dm-node.test', 'non-HA must retain node identity');
        }
    },
    live_appliance_non_ha: {
        data: {
            result: 'ok', role: 'none', mode: 'none', override: 'auto',
            observing: true, reason: '', role_available: true,
            config_available: true, role_mixed: false, carp_aware: true,
            appliance_carp_state: 'absent', appliance_non_ha_confirmed: true,
            carp_vip_count: 0, carp_runtime_available: true,
            carp_runtime_present: false,
            ha_status: 'non_ha', override_active: false,
            non_ha_confirmation: 'appliance_non_ha',
            non_ha_confirmed: true, ha_relevant: false,
            monitoring_scope_ready: false,
            monitoring_scope_reason: 'no_monitored_interfaces',
            monitoring_roles_known: false,
            node: 'OPNsense.internal', node_local: true,
            monitoring_enabled: false, paused_activities: [],
            role_unknown_observation_continues: false,
            last_scan: '2026-11-08 07:37:53', last_scan_state: 'found',
            last_scan_timezone: 'Australia/Sydney',
            monitored_interfaces: [], vips: []
        },
        expect: function (m) {
            check(m.nonHaConfirmed === true,
                'actual .23 appliance-wide CARP absence was not confirmed');
            check(m.haRelevant === false,
                'actual .23 appliance-wide CARP absence retained HA content');
            check(m.summary === 'OPNsense.internal \u00b7 MONITORING_DISABLED',
                'actual .23 confirmed non-HA summary exposed an HA role');
            check(m.summaryWarning === '',
                'actual .23 confirmed non-HA retained an unconfirmed warning');
            check(m.role === 'NON_HA',
                'actual .23 confirmed non-HA did not label the local scope');
            check(m.ownership === 'NODE_LOCAL',
                'actual .23 confirmed non-HA retained CARP-peer wording');
            check(m.activityRelevant === false,
                'actual .23 confirmed non-HA exposed HA activity details');
            check(m.lastScan === 'LAST_SCAN: 2026-11-08 07:37:53 (Australia/Sydney)',
                'actual .23 confirmed non-HA lost last-scan information or timezone');
        }
    },
    live_carp_empty_scope_unconfirmed: {
        data: {
            result: 'ok', role: 'none', mode: 'none', override: 'auto',
            observing: true, reason: '', role_available: true,
            config_available: true, role_mixed: false, carp_aware: true,
            appliance_carp_state: 'present', appliance_non_ha_confirmed: false,
            carp_vip_count: 1, carp_runtime_available: true,
            carp_runtime_present: false,
            ha_status: 'non_ha', override_active: false,
            non_ha_confirmation: 'carp_present_no_monitored_interfaces',
            non_ha_confirmed: false, ha_relevant: true,
            monitoring_scope_ready: false,
            monitoring_scope_reason: 'no_monitored_interfaces',
            monitoring_roles_known: false,
            node: 'OPNsense.internal', node_local: true,
            monitoring_enabled: false, paused_activities: [],
            role_unknown_observation_continues: false,
            last_scan: '2026-11-08 07:37:53', last_scan_state: 'found',
            last_scan_timezone: 'Australia/Sydney',
            monitored_interfaces: [],
            vips: [{vip: '192.0.2.1 (test)', vhid: '1', state: 'unknown'}]
        },
        expect: function (m) {
            check(m.nonHaConfirmed === false,
                'CARP with empty monitoring scope was presented as confirmed non-HA');
            check(m.haRelevant === true,
                'CARP with empty monitoring scope hid HA relevance');
            check(m.role === 'UNCONFIRMED',
                'CARP with empty monitoring scope labelled detection as Non-HA');
            check(m.mode === 'UNCONFIRMED',
                'CARP with empty monitoring scope labelled mode as Non-HA');
            check(m.summary === 'OPNsense.internal \u00b7 HA_STATUS_UNCONFIRMED \u00b7 MONITORING_DISABLED',
                'CARP with empty monitoring scope summary did not distinguish confirmation');
            check(m.summaryWarning === 'CARP_PRESENT_NO_MONITORED_INTERFACES',
                'CARP with empty monitoring scope did not return the scope-specific explanation');
            check(m.ownership === 'NODE_LOCAL',
                'CARP with empty monitoring scope retained CARP-peer wording');
            check(m.lastScan === 'LAST_SCAN: 2026-11-08 07:37:53 (Australia/Sydney)',
                'CARP with empty monitoring scope lost last-scan information or timezone');
            check(m.tone === 'warning',
                'CARP with empty monitoring scope did not distinguish unconfirmed state');
        }
    },
    non_ha_legacy_fallback: {
        data: {
            ha_status: 'non_ha', role: 'none', mode: 'none',
            role_available: true, override: 'auto', monitoring_enabled: true,
            node: 'dm-node.test', last_scan: '2026-11-13 08:25:16',
            last_scan_state: 'found'
        },
        expect: function (m) {
            check(m.nonHaConfirmed === true,
                'legacy positive non-HA response did not derive relevance');
            check(m.haRelevant === false, 'legacy non-HA response retained HA content');
            check(m.summary.indexOf('\u00b7 NON_HA') === -1,
                'legacy non-HA summary still exposed a HA role');
            check(m.ownership === 'NODE_LOCAL',
                'legacy non-HA response retained CARP-peer wording');
            check(m.lastScan.indexOf('TIMEZONE_UNAVAILABLE') !== -1,
                'missing timezone was guessed instead of labelled unavailable');
        }
    },
    non_ha_override_master: {
        data: fixture({
            ha_status: 'master', role: 'none', mode: 'MASTER',
            override: 'master', override_active: true,
            non_ha_confirmed: false, ha_relevant: true
        }),
        expect: function (m) {
            check(m.haRelevant === true, 'active override must retain HA content');
            check(m.overrideActive === true, 'active override not reported');
            check(m.role === 'NON_HA', 'override must preserve detected non-HA role');
            check(m.mode === 'MASTER', 'master override effective mode');
            check(m.summary === 'dm-node.test \u00b7 MASTER \u00b7 MONITORING_ENABLED',
                'override compact line must show effective mode, not detected role');
            check(m.summaryWarning.indexOf('ROLE_OVERRIDE_ACTIVE') !== -1,
                'master override is not visible in the collapsed warning');
            check(m.summaryWarning.indexOf('DETECTED_ROLE') === -1 &&
                m.summaryWarning.indexOf('EFFECTIVE_MODE') === -1,
                'override warning repeats the expanded role facts');
        }
    },
    non_ha_override_backup: {
        data: fixture({
            ha_status: 'backup', role: 'none', mode: 'BACKUP',
            observing: false, paused_activities: paused,
            override: 'backup', override_active: true,
            non_ha_confirmed: false, ha_relevant: true
        }),
        expect: function (m) {
            check(m.haRelevant === true, 'backup override must retain HA content');
            check(m.role === 'NON_HA', 'backup override preserved detected role');
            check(m.mode === 'BACKUP', 'backup override effective mode');
            check(m.paused.length === 6, 'backup override must list paused activities');
            check(m.summaryWarning.indexOf('ROLE_OVERRIDE_ACTIVE') !== -1,
                'backup override is not visible in the summary');
        }
    },
    unavailable: {
        data: fixture({
            ha_status: 'unavailable', role_available: false,
            role: 'none', mode: 'none',
            role_unknown_observation_continues: true
        }),
        expect: function (m) {
            check(m.role === 'UNAVAILABLE', 'unavailable detected role');
            check(m.mode === 'UNAVAILABLE', 'unavailable effective mode');
            check(m.tone === 'danger', 'unavailable tone');
            check(m.summaryWarning === 'ROLE_UNAVAILABLE OBSERVATION_CONTINUES',
                'unavailable summary must carry the backend warning');
            check(m.paused.length === 0, 'unavailable must not invent paused activities');
            check(m.activityRelevant === true,
                'confirmed continuation should retain the activity explanation');
            check(m.summary.indexOf('MONITORING_ENABLED') !== -1,
                'unavailable summary lost the independent monitoring state');
        }
    },
    unavailable_unconfirmed: {
        data: fixture({
            ha_status: 'unavailable', role_available: false,
            role: 'none', mode: 'none',
            role_unknown_observation_continues: false
        }),
        expect: function (m) {
            check(m.summaryWarning === 'ROLE_UNAVAILABLE',
                'unavailable state must not infer observation policy');
            check(m.activityRelevant === false,
                'unconfirmed continuation must not show an activity claim');
        }
    },
    fetch_failed: {
        data: fixture({
            ha_status: 'fetch_failed', fetch_failed: true,
            role_available: false, role: 'none', mode: 'NONE',
            node: '', last_scan: '', last_scan_state: 'unavailable',
            role_unknown_observation_continues: false
        }),
        expect: function (m) {
            check(m.role === 'UNAVAILABLE', 'fetch failure role');
            check(m.mode === 'UNAVAILABLE', 'fetch failure effective mode');
            check(m.tone === 'danger', 'fetch failure tone');
            check(m.summaryWarning === 'FETCH_FAILED',
                'fetch failure summary must warn instead of implying a role');
            check(m.summaryWarning.indexOf('OBSERVATION_CONTINUES') === -1,
                'fetch failure invented operational gating');
            check(m.activityRelevant === false,
                'fetch failure invented an activity explanation');
            check(m.lastScan === 'SCAN_FETCH_FAILED',
                'fetch failure did not identify unavailable scan retrieval');
        }
    },
    scan_none: {
        data: fixture({last_scan: '', last_scan_state: 'none'}),
        expect: function (m) {
            check(m.lastScan === 'NO_SCAN', 'empty successful history wording');
        }
    },
    scan_unavailable: {
        data: fixture({last_scan: '', last_scan_state: 'unavailable'}),
        expect: function (m) {
            check(m.lastScan === 'SCAN_UNAVAILABLE',
                'unreadable successful history wording');
        }
    },
    unavailable_awareness_off: {
        data: fixture({
            ha_status: 'unavailable', role_available: false,
            role: 'none', mode: 'none', carp_aware: false
        }),
        expect: function (m) {
            check(m.role === 'UNAVAILABLE', 'awareness-off unavailable detected role');
            check(m.mode === 'UNAVAILABLE', 'awareness-off unavailable effective mode');
            check(m.summaryWarning === 'ROLE_UNAVAILABLE AWARENESS_OFF',
                'awareness-off unavailable must not claim fail-open gating');
            check(m.paused.length === 0, 'awareness-off unavailable invented a pause');
        }
    },
    mixed: {
        data: fixture({
            ha_status: 'master', role: 'MASTER', mode: 'MASTER',
            role_mixed: true
        }),
        expect: function (m) {
            check(m.role === 'MASTER / BACKUP', 'mixed detected role');
            check(m.mode === 'MASTER', 'mixed effective mode must follow daemon precedence');
            check(m.paused.length === 0, 'mixed MASTER state must continue observing');
        }
    },
    override_master: {
        data: fixture({
            ha_status: 'master', role: 'BACKUP', mode: 'MASTER',
            override: 'master', override_active: true
        }),
        expect: function (m) {
            check(m.role === 'BACKUP', 'override must not rewrite detected role');
            check(m.mode === 'MASTER', 'override master effective mode');
            check(m.paused.length === 0, 'override master must not pause');
            check(m.overrideActive === true, 'master override not reported');
            check(m.ownership === 'OWNERSHIP',
                'master override must retain CARP-peer context');
            check(m.summaryWarning.indexOf('ROLE_OVERRIDE_ACTIVE') !== -1,
                'master override missing from summary');
            check(m.summaryWarning.indexOf('EFFECTIVE_MODE') === -1,
                'master override warning repeats the compact effective mode');
        }
    },
    override_backup: {
        data: fixture({
            ha_status: 'backup', role: 'MASTER', mode: 'BACKUP',
            observing: false, paused_activities: paused,
            override: 'backup', override_active: true
        }),
        expect: function (m) {
            check(m.role === 'MASTER', 'backup override must preserve detected MASTER');
            check(m.mode === 'BACKUP', 'backup override effective mode');
            check(m.paused.length === 6, 'backup override pauses exact activities');
            check(m.overrideActive === true, 'backup override not reported');
            check(m.summaryWarning.indexOf('ROLE_OVERRIDE_ACTIVE') !== -1,
                'backup override warning missing from the collapsed state');
        }
    },
    awareness_off: {
        data: fixture({
            ha_status: 'backup', role: 'BACKUP', mode: 'BACKUP',
            carp_aware: false
        }),
        expect: function (m) {
            check(m.role === 'BACKUP', 'awareness-off detected role');
            check(m.mode === 'BACKUP', 'awareness-off effective mode');
            check(m.paused.length === 0, 'awareness-off must not pause');
            check(m.summaryWarning === 'AWARENESS_OFF',
                'awareness-off explanation must remain visible when collapsed');
            check(m.summary.indexOf('AWARENESS_OFF') === -1,
                'awareness-off explanation must not repeat in the summary');
        }
    },
    awareness_off_non_ha: {
        data: fixture({
            ha_status: 'non_ha', role: 'none', mode: 'none',
            carp_aware: false, override: 'auto', override_active: false,
            non_ha_confirmed: true, ha_relevant: false
        }),
        expect: function (m) {
            check(m.haRelevant === false,
                'awareness-off non-HA must still hide HA-specific content');
            check(m.nonHaConfirmed === true,
                'awareness-off non-HA must retain confirmed detector state');
            check(m.paused.length === 0, 'awareness-off non-HA invented pauses');
            check(m.lastScan === 'LAST_SCAN: 2026-11-13 08:25:16 (Australia/Sydney)',
                'awareness-off non-HA lost scan information or timezone');
        }
    },
    override_with_detector_error: {
        data: fixture({
            ha_status: 'backup', role: 'none', mode: 'BACKUP',
            role_available: false, observing: false,
            paused_activities: paused, override: 'backup', override_active: true
        }),
        expect: function (m) {
            check(m.role === 'UNAVAILABLE', 'override must show unavailable detection');
            check(m.mode === 'BACKUP', 'override backup effective mode');
            check(m.paused.length === 6, 'override backup pauses exact activities');
            check(m.summaryWarning.indexOf('ROLE_CHECK_FAILED') !== -1,
                'override detector warning');
            check(m.summaryWarning.indexOf('ROLE_OVERRIDE_ACTIVE') !== -1,
                'detector-error override warning missing');
        }
    },
    override_unavailable_awareness_off: {
        data: fixture({
            ha_status: 'backup', role: 'none', mode: 'BACKUP',
            role_available: false, carp_aware: false,
            override: 'backup', override_active: true
        }),
        expect: function (m) {
            check(m.role === 'UNAVAILABLE', 'awareness-off override detector role');
            check(m.mode === 'BACKUP', 'awareness-off override effective mode');
            check(m.paused.length === 0, 'awareness-off override must not pause');
            check(m.summaryWarning === 'ROLE_OVERRIDE_ACTIVE AWARENESS_OFF ROLE_CHECK_FAILED',
                'awareness-off override must explain both settings');
        }
    },
    legacy_response: {
        data: {role: 'MASTER', mode: 'MASTER', observing: true},
        expect: function (m) {
            check(m.role === 'MASTER', 'legacy response role fallback');
            check(m.mode === 'MASTER', 'legacy response mode fallback');
        }
    }
};

let count = 0;
Object.keys(cases).forEach(function (name) {
    const test = cases[name];
    const fromDevices = devicesModel(test.data, t);
    const fromSettings = settingsModel(test.data, t);
    test.expect(fromDevices);
    check(
        JSON.stringify(fromDevices) === JSON.stringify(fromSettings),
        name + ': Devices and Settings state models differ'
    );
    count += 1;
});

console.log('PREVIEW_MASTER=' + JSON.stringify(devicesModel(cases.master.data, previewT)));
console.log('PREVIEW_BACKUP=' + JSON.stringify(devicesModel(cases.backup.data, previewT)));
console.log('PREVIEW_NON_HA=' + JSON.stringify(devicesModel(cases.non_ha.data, previewT)));
console.log('PREVIEW_LIVE_APPLIANCE_NON_HA=' + JSON.stringify(devicesModel(cases.live_appliance_non_ha.data, previewT)));
console.log('PREVIEW_CARP_EMPTY_SCOPE_UNCONFIRMED=' + JSON.stringify(devicesModel(cases.live_carp_empty_scope_unconfirmed.data, previewT)));
console.log('PREVIEW_NON_HA_OVERRIDE=' + JSON.stringify(devicesModel(cases.non_ha_override_master.data, previewT)));
console.log('PREVIEW_UNAVAILABLE=' + JSON.stringify(devicesModel(cases.unavailable.data, previewT)));
console.log('PREVIEW_REFRESH_FAILURE=' + JSON.stringify(devicesModel({
    ha_status: 'fetch_failed',
    fetch_failed: true,
    role_available: false,
    role: 'none',
    mode: 'NONE',
    carp_aware: true,
    paused_activities: [],
    node: '',
    last_scan: '',
    last_scan_state: 'unavailable'
}, previewT)));

function checkLoader(viewPath) {
    let options = null;
    const calls = [];
    const controlCalls = [];
    const sandbox = {
        $: {
            ajax: function (opts) {
                options = opts;
            }
        },
        renderHaNotice: function (data) {
            calls.push({kind: 'notice', data: data});
        },
        renderHaStatus: function (data, unavailable) {
            calls.push({kind: 'status', data: data, unavailable: unavailable});
        },
        updateHaControls: function (data) {
            controlCalls.push(data);
        },
        haStatusRequest: 0
    };
    const load = loadFunction(viewPath, 'loadHaNodeVisibility', sandbox);

    load();
    check(options !== null, viewPath + ': loader did not issue one AJAX request');
    check(options.url === '/api/devicemonitor/config/getcarpstatus',
        viewPath + ': loader does not use the existing status API');
    check(options.type === 'GET', viewPath + ': loader is not read-only GET');
    check(options.cache === false, viewPath + ': loader may reuse cached status');
    check(options.timeout === 10000, viewPath + ': loader has no bounded timeout');

    const sample = fixture({ha_status: 'master', role: 'MASTER', mode: 'MASTER'});
    options.success(sample);

    const expectedCalls = viewPath === settingsPath ? 2 : 1;
    check(calls.length === expectedCalls, viewPath + ': success did not render every status view');
    check(calls[0].kind === 'notice' && calls[0].data === sample,
        viewPath + ': notice did not receive the API response');
    if (viewPath === settingsPath) {
        check(calls[1].kind === 'status' && calls[1].data === sample && calls[1].unavailable === false,
            viewPath + ': HA/CARP table did not receive the same API response');
        check(controlCalls.length === 1 && controlCalls[0] === sample,
            viewPath + ': relevance did not update the HA controls');
    }

    calls.length = 0;
    controlCalls.length = 0;
    options.error();
    check(calls.length === expectedCalls, viewPath + ': failure did not clear every status view');
    check(calls[0].kind === 'notice' &&
        calls[0].data.ha_status === 'fetch_failed' &&
        calls[0].data.fetch_failed === true &&
        calls[0].data.role_available === false &&
        calls[0].data.last_scan_state === 'unavailable',
        viewPath + ': failed refresh left a stale role visible');
    if (viewPath === settingsPath) {
        check(calls[1].kind === 'status' && calls[1].unavailable === true,
            viewPath + ': failed refresh left a stale VIP table visible');
        check(controlCalls.length === 1 && controlCalls[0] === null,
            viewPath + ': failed refresh did not restore unknown-state controls');
    }

    calls.length = 0;
    controlCalls.length = 0;
    load();
    const superseded = options;
    load();
    const current = options;
    current.error();
    calls.length = 0;
    controlCalls.length = 0;
    superseded.success(sample);
    check(calls.length === 0,
        viewPath + ': superseded success restored an old role after a failed refresh');
    check(controlCalls.length === 0,
        viewPath + ': superseded success changed controls after a failed refresh');

    const source = fs.readFileSync(viewPath, 'utf8');
    check(source.indexOf('setInterval(loadHaNodeVisibility, 30000)') !== -1,
        viewPath + ': notice does not refresh without Apply');
    check(source.indexOf('loadHaNodeVisibility();') !== -1,
        viewPath + ': notice not loaded on page start');
    check((source.match(/getcarpstatus/g) || []).length === 1,
        viewPath + ': more than one status-source request path');
    check(source.indexOf('loadHaStatus') === -1,
        viewPath + ': obsolete duplicate status loader remains');
    check(source.indexOf('requestId !== haStatusRequest') !== -1,
        viewPath + ': superseded refresh response can overwrite current state');
    return source;
}

checkLoader(devicesPath);
const settingsSource = checkLoader(settingsPath);

check(
    settingsSource.indexOf("$('#btn-ha-status-refresh').click(loadHaNodeVisibility)") !== -1,
    'Settings: manual refresh does not use the shared status loader'
);
check(
    settingsSource.indexOf("$('a[href=\"#tab-ha\"]').on('shown.bs.tab', loadHaNodeVisibility)") !== -1,
    'Settings: opening HA / CARP does not use the shared status loader'
);
check(
    settingsSource.indexOf('var haStatusRequest = 0;') <
        settingsSource.indexOf('loadHaNodeVisibility();'),
    'Settings: request state is initialised after the first status load'
);
check(
    settingsSource.indexOf("$('#ha-status-vips').empty()") !== -1,
    'Settings: failed refresh cannot clear the old VIP rows'
);
check(
    /unavailable\s*\?\s*translations\.status_unknown/.test(settingsSource),
    'Settings: failed refresh can leave a stale observation verdict'
);
check(
    settingsSource.indexOf("devicemonitor_t('HA policy permission')") !== -1 &&
        settingsSource.indexOf('service_observation') === -1,
    'Settings: HA policy permission is not distinguished from actual monitoring'
);
check(
    settingsSource.indexOf('translations.status_permitted') !== -1 &&
        settingsSource.indexOf('translations.status_paused_by_ha') !== -1 &&
        settingsSource.indexOf('translations.status_observing') === -1,
    'Settings: permission values still imply that observation is running'
);

function checkToggleMarkup(viewPath) {
    const source = fs.readFileSync(viewPath, 'utf8');

    check(source.indexOf('<button type="button" id="dm-ha-node-toggle"') !== -1,
        viewPath + ': details toggle is not a native button');
    check(source.indexOf('aria-expanded="false"') !== -1,
        viewPath + ': details toggle does not start collapsed');
    check(source.indexOf('aria-controls="dm-ha-node-details"') !== -1,
        viewPath + ': details toggle does not name its controlled region');
    check(source.indexOf('<div id="dm-ha-node-details" class="dm-ha-node-details" hidden>') !== -1,
        viewPath + ': details region is not hidden by default');
    check(/dm-ha-node-toggle[\s\S]{0,220}devicemonitor_t\('Show details'\)/.test(source),
        viewPath + ': collapsed toggle label is not translated');
    check(source.indexOf('tabindex="-1"') === -1,
        viewPath + ': native toggle was removed from the tab order');
    const toggleTag = source.match(/<button type="button" id="dm-ha-node-toggle"[\s\S]*?<\/button>/);
    check(toggleTag && toggleTag[0].indexOf('disabled') === -1,
        viewPath + ': details toggle may be disabled');
    check(source.indexOf("$('#dm-ha-node-toggle').on('click'") !== -1,
        viewPath + ': details toggle has no click handler');
    check(/event\.preventDefault\(\);[\s\S]{0,80}toggleHaNotice\(\);/.test(source),
        viewPath + ': details toggle can submit or navigate');
    check(/dm-ha-node-notice-head[\s\S]{0,500}id="dm-ha-node-summary"[\s\S]{0,500}id="dm-ha-node-toggle"/.test(source),
        viewPath + ': compact summary and toggle are not in the same head row');
    check(/id="dm-ha-node-summary-warning"[\s\S]{0,200}id="dm-ha-node-details"/.test(source),
        viewPath + ': collapsed warning is not outside the details region');
    check(source.indexOf('id="dm-ha-node-role-facts"') > source.indexOf('id="dm-ha-node-details"'),
        viewPath + ': role facts escaped the expanded details region');
    check(source.indexOf('dm-ha-node-notice-facts') === -1,
        viewPath + ': obsolete duplicate collapsed fact row remains');
    check(source.indexOf('id="dm-ha-node-message"') === -1 &&
        source.indexOf('id="dm-ha-node-monitoring-note"') === -1,
        viewPath + ': expanded area still contains duplicate status messages');
    check(/\.dm-ha-node-notice-head\s*\{[^}]*flex-wrap:wrap/.test(source) &&
        /\.dm-ha-node-summary\s*\{[^}]*overflow-wrap:anywhere/.test(source),
        viewPath + ': compact notice cannot wrap naturally on narrow screens');
    check(source.indexOf('.dm-ha-node-role-facts[hidden] { display:none; }') !== -1,
        viewPath + ': hidden role facts can be overridden by display:flex');
}

function makeJqueryStub() {
    const elements = {};

    function element(selector) {
        if (!elements[selector]) {
            elements[selector] = {
                text: '',
                attrs: {},
                hidden: false,
                display: '',
                classes: []
            };
        }
        return elements[selector];
    }

    function $(selector) {
        if (typeof selector === 'string' && selector.charAt(0) === '<') {
            return {
                text: function () { return this; }
            };
        }
        const node = element(selector);
        return {
            text: function (value) {
                if (value === undefined) { return node.text; }
                node.text = value;
                return this;
            },
            attr: function (name, value) {
                if (value === undefined) { return node.attrs[name]; }
                node.attrs[name] = value;
                return this;
            },
            prop: function (name, value) {
                if (value === undefined) { return node[name]; }
                node[name] = value;
                return this;
            },
            toggle: function (show) {
                node.display = show ? '' : 'none';
                return this;
            },
            removeClass: function (name) {
                node.classes = node.classes.filter(function (item) { return item !== name; });
                return this;
            },
            addClass: function (name) {
                node.classes.push(name);
                return this;
            },
            empty: function () { return this; },
            append: function () { return this; }
        };
    }

    return { $: $, elements: elements };
}

function checkToggleBehaviour(viewPath) {
    const source = fs.readFileSync(viewPath, 'utf8');
    const snippets = [
        extractFunction(source, 'buildHaNoticeModel'),
        extractFunction(source, 'setHaNoticeExpanded'),
        extractFunction(source, 'toggleHaNotice'),
        extractFunction(source, 'renderHaNotice')
    ].join('\n');
    const dom = makeJqueryStub();
    const sandbox = {
        $: dom.$,
        translations: t,
        haNoticeExpanded: false
    };

    vm.runInNewContext(
        snippets + '\nthis.setExpanded = setHaNoticeExpanded;'
            + 'this.toggleExpanded = toggleHaNotice;'
            + 'this.renderNotice = renderHaNotice;',
        sandbox
    );

    sandbox.setExpanded(false);
    check(dom.elements['#dm-ha-node-toggle'].attrs['aria-expanded'] === 'false',
        viewPath + ': collapsed aria-expanded is not false');
    check(dom.elements['#dm-ha-node-toggle-label'].text === 'SHOW_DETAILS',
        viewPath + ': collapsed label is not Show details');
    check(dom.elements['#dm-ha-node-details'].hidden === true,
        viewPath + ': collapsed details remain visible');
    check(dom.elements['#dm-ha-node-details'].display === 'none',
        viewPath + ': collapsed details retain display');

    sandbox.setExpanded(true);
    check(dom.elements['#dm-ha-node-toggle'].attrs['aria-expanded'] === 'true',
        viewPath + ': expanded aria-expanded is not true');
    check(dom.elements['#dm-ha-node-toggle-label'].text === 'HIDE_DETAILS',
        viewPath + ': expanded label is not Hide details');
    check(dom.elements['#dm-ha-node-details'].hidden === false,
        viewPath + ': expanded details remain hidden');

    sandbox.renderNotice(cases.master.data);
    check(dom.elements['#dm-ha-node-details'].hidden === false &&
        dom.elements['#dm-ha-node-toggle'].attrs['aria-expanded'] === 'true',
        viewPath + ': refresh collapsed an expanded notice');
    check(dom.elements['#dm-ha-node-summary'].text ===
        'dm-node.test \u00b7 MASTER \u00b7 MONITORING_ENABLED',
        viewPath + ': refresh did not update the compact summary immediately');

    sandbox.renderNotice(cases.non_ha.data);
    check(dom.elements['#dm-ha-node-details'].hidden === false,
        viewPath + ': non-HA refresh collapsed the expanded notice');
    check(dom.elements['#dm-ha-node-summary'].display === '',
        viewPath + ': non-HA summary was hidden');
    check(dom.elements['#dm-ha-node-summary'].text ===
        'dm-node.test \u00b7 MONITORING_ENABLED',
        viewPath + ': non-HA summary retained the HA role');
    check(dom.elements['#dm-ha-node-role-facts'].display === 'none',
        viewPath + ': non-HA role facts were not hidden');
    check(dom.elements['#dm-ha-node-activity-details'].display === 'none',
        viewPath + ': non-HA activity explanation was not hidden');
    check(dom.elements['#dm-ha-node-ownership'].text === 'NODE_LOCAL',
        viewPath + ': non-HA CARP-peer wording was not replaced with node-local wording');
    check(dom.elements['#dm-ha-node-last-scan'].text ===
        'LAST_SCAN: 2026-11-13 08:25:16 (Australia/Sydney)',
        viewPath + ': non-HA refresh lost last-scan information or timezone');

    sandbox.renderNotice(cases.live_carp_empty_scope_unconfirmed.data);
    check(dom.elements['#dm-ha-node-summary'].text ===
        'OPNsense.internal \u00b7 HA_STATUS_UNCONFIRMED \u00b7 MONITORING_DISABLED',
        viewPath + ': CARP empty-scope response was rendered as confirmed non-HA');
    check(dom.elements['#dm-ha-node-role'].text === 'UNCONFIRMED' &&
        dom.elements['#dm-ha-node-mode'].text === 'UNCONFIRMED',
        viewPath + ': CARP empty-scope response reused the Non-HA role label');
    check(dom.elements['#dm-ha-node-summary-warning'].text === 'CARP_PRESENT_NO_MONITORED_INTERFACES' &&
        dom.elements['#dm-ha-node-summary-warning'].display === '',
        viewPath + ': CARP empty-scope reason was not visible while collapsed');
    check(dom.elements['#dm-ha-node-role-facts'].display === '',
        viewPath + ': CARP empty-scope state hid detection details');
    check(dom.elements['#dm-ha-node-ownership'].text === 'NODE_LOCAL',
        viewPath + ': CARP empty-scope state retained CARP-peer wording');

    sandbox.renderNotice(cases.live_appliance_non_ha.data);
    check(dom.elements['#dm-ha-node-summary'].text ===
        'OPNsense.internal \u00b7 MONITORING_DISABLED',
        viewPath + ': actual .23 appliance proof was rendered as unconfirmed');
    check(dom.elements['#dm-ha-node-role-facts'].display === 'none',
        viewPath + ': actual .23 appliance proof left role facts visible');
    check(dom.elements['#dm-ha-node-summary-warning'].display === 'none',
        viewPath + ': actual .23 appliance proof left a warning visible');

    sandbox.renderNotice(fixture({
        ha_status: 'non_ha', override: 'auto', override_active: false,
        non_ha_confirmed: true, ha_relevant: false, monitoring_enabled: false
    }));
    check(dom.elements['#dm-ha-node-summary'].text ===
        'dm-node.test \u00b7 MONITORING_DISABLED',
        viewPath + ': non-HA monitoring-enabled state was not updated');

    sandbox.renderNotice(cases.backup.data);
    check(dom.elements['#dm-ha-node-details'].hidden === false,
        viewPath + ': BACKUP refresh collapsed the expanded notice');
    check(dom.elements['#dm-ha-node-summary'].display === '',
        viewPath + ': BACKUP did not restore the HA summary');
    check(dom.elements['#dm-ha-node-role-facts'].display === '',
        viewPath + ': BACKUP did not restore the HA role facts');
    check(dom.elements['#dm-ha-node-activity-details'].display === '',
        viewPath + ': BACKUP did not restore the activity explanation');
    check(dom.elements['#dm-ha-node-summary'].text.indexOf('SOME_ACTIVITIES_PAUSED') !== -1,
        viewPath + ': BACKUP refresh did not show the compact paused indicator');

    sandbox.renderNotice(cases.unavailable.data);
    check(dom.elements['#dm-ha-node-summary-warning'].display === '',
        viewPath + ': unavailable warning was hidden in the collapsed state');
    sandbox.renderNotice(cases.non_ha_override_master.data);
    check(dom.elements['#dm-ha-node-summary-warning'].text.indexOf('ROLE_OVERRIDE_ACTIVE') !== -1 &&
        dom.elements['#dm-ha-node-summary-warning'].display === '',
        viewPath + ': override warning was hidden in the collapsed state');

    sandbox.toggleExpanded();
    check(dom.elements['#dm-ha-node-toggle'].attrs['aria-expanded'] === 'false' &&
        dom.elements['#dm-ha-node-details'].hidden === true,
        viewPath + ': Hide details did not collapse both states');

    check(extractFunction(source, 'renderHaNotice').indexOf('setHaNoticeExpanded') === -1,
        viewPath + ': refresh path can reset the expansion state');
    const togglePath = extractFunction(source, 'setHaNoticeExpanded')
        + extractFunction(source, 'toggleHaNotice');
    check(togglePath.indexOf('submit(') === -1,
        viewPath + ': notice path can submit settings');
}

function checkRelevanceControls(settingsSource) {
    check(settingsSource.indexOf('No CARP configuration detected') !== -1,
        'Settings: confirmed non-HA explanation is missing');
    check(settingsSource.indexOf('href="#tab-ha"') !== -1 &&
        settingsSource.indexOf('id="tab-ha"') !== -1,
        'Settings: HA / CARP tab is no longer accessible');
    check(/id="ha_role_override"[\s\S]*?class="selectpicker"[\s\S]*?data-style="btn-default"[\s\S]*?<option value="auto">/.test(settingsSource),
        'Settings: role override no longer uses the standard OPNsense select treatment');
    check(!/id="ha_role_override"[\s\S]{0,500}(?:font-family|font-size)/.test(settingsSource),
        'Settings: role override reintroduced a control-specific font override');
    check(settingsSource.indexOf("devicemonitor_t('Automatic (use CARP role)')") !== -1 &&
        settingsSource.indexOf("devicemonitor_t('Force MASTER behaviour')") !== -1 &&
        settingsSource.indexOf("devicemonitor_t('Force BACKUP behaviour')") !== -1 &&
        settingsSource.indexOf('value="auto"') !== -1 &&
        settingsSource.indexOf('value="master"') !== -1 &&
        settingsSource.indexOf('value="backup"') !== -1,
        'Settings: role override labels or persisted values changed unexpectedly');
    check(settingsSource.indexOf('Overrides Device Monitor behaviour only; does not change the firewall’s CARP role.') !== -1,
        'Settings: role override scope help text is missing');
    check(settingsSource.indexOf('never observe') === -1,
        'Settings: BACKUP override still claims that all observation stops');
    check(settingsSource.indexOf("ha_carp_enabled: $('#ha_carp_enabled').is(':checked')?'1':'0'") !== -1 &&
        settingsSource.indexOf("ha_role_override: $('#ha_role_override').val()") !== -1 &&
        settingsSource.indexOf("ha_notify_failover: $('#ha_notify_failover').is(':checked')?'1':'0'") !== -1,
        'Settings: disabled HA controls are no longer included in saves');

    const nodes = {
        '#ha_carp_enabled': {disabled: false, checked: true},
        '#ha_notify_failover': {disabled: false, checked: true},
        '#ha_role_override': {disabled: false, value: 'auto'},
        '#dm-ha-non-ha-note': {display: 'none'}
    };
    const refreshStates = [];
    const $ = function (selector) {
        const node = nodes[selector];
        check(node !== undefined, 'Settings: control stub missing ' + selector);
        return {
            val: function (value) {
                if (value === undefined) { return node.value; }
                node.value = value;
                return this;
            },
            prop: function (name, value) {
                if (value === undefined) { return node[name]; }
                node[name] = value;
                return this;
            },
            toggle: function (show) {
                node.display = show ? '' : 'none';
                return this;
            }
        };
    };
    const sandbox = {
        $: $,
        lastHaStatusData: null,
        refreshHaRoleOverrideSelectpicker: function () {
            refreshStates.push({
                carpDisabled: nodes['#ha_carp_enabled'].disabled,
                notifyDisabled: nodes['#ha_notify_failover'].disabled,
                overrideDisabled: nodes['#ha_role_override'].disabled
            });
        }
    };
    vm.runInNewContext(
        extractFunction(settingsSource, 'updateHaControls')
            + '\nthis.update = updateHaControls;',
        sandbox
    );

    sandbox.update({non_ha_confirmed: true});
    check(nodes['#ha_carp_enabled'].disabled === true,
        'Settings: confirmed non-HA left CARP awareness enabled');
    check(nodes['#ha_notify_failover'].disabled === true,
        'Settings: confirmed non-HA left failover notification enabled');
    check(nodes['#ha_role_override'].disabled === false,
        'Settings: confirmed non-HA disabled the role override');
    check(nodes['#ha_carp_enabled'].checked === true &&
        nodes['#ha_notify_failover'].checked === true &&
        nodes['#ha_role_override'].value === 'auto',
        'Settings: non-HA gating changed saved control values');
    check(nodes['#dm-ha-non-ha-note'].display === '',
        'Settings: confirmed non-HA explanation was not shown');
    check(refreshStates.length === 1 && refreshStates[0].overrideDisabled === false,
        'Settings: disabled-state update did not refresh the role override selectpicker');

    nodes['#ha_role_override'].value = 'master';
    sandbox.update({non_ha_confirmed: true});
    check(nodes['#ha_carp_enabled'].disabled === false &&
        nodes['#ha_notify_failover'].disabled === false,
        'Settings: explicit override did not re-enable CARP controls');
    check(nodes['#ha_role_override'].disabled === false,
        'Settings: explicit override became uneditable');
    check(nodes['#dm-ha-non-ha-note'].display === 'none',
        'Settings: explicit override left the non-HA explanation visible');
    check(refreshStates.length === 2 && refreshStates[1].overrideDisabled === false,
        'Settings: enabled-state update did not refresh the role override selectpicker');

    sandbox.update({ha_status: 'fetch_failed', non_ha_confirmed: false});
    check(nodes['#ha_carp_enabled'].disabled === false &&
        nodes['#ha_notify_failover'].disabled === false,
        'Settings: status failure disabled CARP controls');
    check(nodes['#ha_role_override'].disabled === false,
        'Settings: status failure disabled the role override');

    sandbox.update(null);
    check(nodes['#ha_carp_enabled'].disabled === false &&
        nodes['#ha_notify_failover'].disabled === false &&
        nodes['#dm-ha-non-ha-note'].display === 'none',
        'Settings: unknown state was treated as non-HA');

    const fn = extractFunction(settingsSource, 'updateHaControls');
    check(fn.indexOf(".prop('checked'") === -1 && !/\.val\(\s*[^)]/.test(fn),
        'Settings: relevance gating can rewrite saved values');
}

function checkHaRoleOverrideSelectpicker(settingsSource) {
    const helper = extractFunction(settingsSource, 'refreshHaRoleOverrideSelectpicker');
    const loadConfig = extractFunction(settingsSource, 'loadConfig');
    const update = extractFunction(settingsSource, 'updateHaControls');

    check(helper.indexOf("$select.selectpicker();") !== -1 &&
        helper.indexOf("$select.selectpicker('refresh');") !== -1,
        'Settings: role override selectpicker is not explicitly initialised and refreshed');
    check(helper.indexOf("closest('.bootstrap-select')") !== -1 &&
        helper.indexOf('button.dropdown-toggle') !== -1,
        'Settings: generated selectpicker button is not synchronised');
    check(helper.indexOf("attr('aria-label'") !== -1 &&
        helper.indexOf("attr('tabindex'") === -1,
        'Settings: selectpicker accessible label or plugin-managed focus proxy changed incorrectly');
    check(/id="ha_role_override"[\s\S]*?\btabindex="0"[\s\S]*?aria-label=/.test(settingsSource),
        'Settings: native select is not the Bootstrap-select keyboard focus proxy');
    check(helper.indexOf('keydown.dmHaSelectpicker') !== -1 &&
        helper.indexOf('event.which === 32') !== -1 &&
        helper.indexOf('event.which === 13') !== -1 &&
        helper.indexOf("trigger('click.bs.dropdown.data-api')") !== -1,
        'Settings: closed selectpicker does not explicitly open on Space or Enter');
    check(helper.indexOf('.val(') === -1,
        'Settings: selectpicker refresh can rewrite the saved role value');
    check(helper.indexOf('submit') === -1 && helper.indexOf('.btn-apply') === -1,
        'Settings: opening or refreshing the selectpicker can submit settings');

    const valueAt = loadConfig.indexOf("$('#ha_role_override').val(");
    const refreshAt = loadConfig.indexOf('refreshHaRoleOverrideSelectpicker();', valueAt);
    check(valueAt !== -1 && refreshAt > valueAt,
        'Settings: async config load does not refresh the selectpicker after setting its value');
    check(update.indexOf('refreshHaRoleOverrideSelectpicker();') !== -1,
        'Settings: role-control disabled state is not reflected in the selectpicker');
    check(settingsSource.indexOf("$('.dm-pane-form').on('submit', function(e) { e.preventDefault(); });") !== -1,
        'Settings: pane form submit prevention was removed');
    check(settingsSource.indexOf('    refreshHaRoleOverrideSelectpicker();\n    /* All five configuration panes') !== -1,
        'Settings: role override selectpicker is not initialised before asynchronous loads');

    const state = {
        value: 'auto',
        initialized: false,
        calls: [],
        attrs: {tabindex: '-1'},
        open: false,
        keydown: null,
        triggered: [],
        prevented: 0,
        stopped: 0
    };
    const optionText = {
        auto: 'Automatic (use CARP role)',
        master: 'Force MASTER behaviour',
        backup: 'Force BACKUP behaviour'
    };
    const toggle = {
        length: 1,
        attr: function (name, value) {
            if (value === undefined) { return state.attrs[name]; }
            state.attrs[name] = value;
            return this;
        },
        off: function (namespace) {
            check(namespace === 'keydown.dmHaSelectpicker',
                'Settings: wrong keyboard handler namespace');
            state.keydown = null;
            return this;
        },
        on: function (namespace, handler) {
            check(namespace === 'keydown.dmHaSelectpicker',
                'Settings: wrong keyboard handler namespace');
            state.keydown = handler;
            return this;
        },
        closest: function (selector) {
            check(selector === '.bootstrap-select',
                'Settings: wrong toggle container selector');
            return {
                hasClass: function (name) {
                    check(name === 'open', 'Settings: wrong open-state class');
                    return state.open;
                }
            };
        },
        trigger: function (eventName) {
            check(eventName === 'click.bs.dropdown.data-api',
                'Settings: wrong selectpicker open event');
            state.triggered.push(eventName);
            state.open = true;
            return this;
        }
    };
    const select = {
        length: 1,
        data: function (key) {
            check(key === 'selectpicker', 'Settings: unexpected data key ' + key);
            return state.initialized ? {} : undefined;
        },
        selectpicker: function (action) {
            state.calls.push(action || 'init');
            if (!action) { state.initialized = true; }
            return this;
        },
        closest: function (selector) {
            check(selector === '.bootstrap-select', 'Settings: wrong selectpicker container selector');
            return {
                children: function (selector) {
                    check(selector === 'button.dropdown-toggle',
                        'Settings: wrong selectpicker toggle selector');
                    return toggle;
                }
            };
        },
        attr: function (name) {
            if (name === 'aria-label') { return 'Role override'; }
            return undefined;
        },
        find: function (selector) {
            check(selector === 'option:selected', 'Settings: wrong selected-option selector');
            return {text: function () { return optionText[state.value]; }};
        }
    };
    const sandbox = {
        $: function (selector) {
            check(selector === '#ha_role_override', 'Settings: wrong role override selector');
            return select;
        }
    };
    vm.runInNewContext(
        helper + '\nthis.refresh = refreshHaRoleOverrideSelectpicker;',
        sandbox
    );

    sandbox.refresh();
    check(state.calls.join(',') === 'init,refresh',
        'Settings: selectpicker was not initialised then refreshed');
    check(state.value === 'auto' && state.attrs.tabindex === '-1' &&
        state.attrs['aria-label'] === 'Role override: Automatic (use CARP role)',
        'Settings: initial selectpicker value, plugin focus proxy or label is incorrect');
    check(typeof state.keydown === 'function',
        'Settings: closed-state keyboard handler was not installed');

    let event = {
        which: 32,
        preventDefault: function () { state.prevented += 1; },
        stopPropagation: function () { state.stopped += 1; }
    };
    state.keydown(event);
    check(state.prevented === 1 && state.stopped === 1 &&
        state.triggered.join(',') === 'click.bs.dropdown.data-api' && state.open === true,
        'Settings: Space did not open the closed selectpicker');

    state.prevented = 0;
    state.stopped = 0;
    state.triggered = [];
    state.keydown(event);
    check(state.prevented === 0 && state.stopped === 0 && state.triggered.length === 0,
        'Settings: local Space handler intercepted selection while the menu was open');

    state.open = false;
    event = {
        which: 13,
        preventDefault: function () { state.prevented += 1; },
        stopPropagation: function () { state.stopped += 1; }
    };
    state.keydown(event);
    check(state.prevented === 1 && state.stopped === 1 &&
        state.triggered.join(',') === 'click.bs.dropdown.data-api',
        'Settings: Enter did not open the closed selectpicker');

    state.value = 'master';
    sandbox.refresh();
    check(state.calls.join(',') === 'init,refresh,refresh',
        'Settings: selectpicker did not refresh after an async value/state change');
    check(state.value === 'master' && state.attrs.tabindex === '-1' &&
        state.attrs['aria-label'] === 'Role override: Force MASTER behaviour' &&
        typeof state.keydown === 'function',
        'Settings: refreshed selectpicker did not preserve its value or keyboard proxy');

    state.value = 'backup';
    sandbox.refresh();
    check(state.attrs.tabindex === '-1' &&
        state.attrs['aria-label'] === 'Role override: Force BACKUP behaviour',
        'Settings: refreshed selectpicker changed the plugin-owned tab index');
}

checkToggleMarkup(devicesPath);
checkToggleMarkup(settingsPath);
checkToggleBehaviour(devicesPath);
checkToggleBehaviour(settingsPath);
checkRelevanceControls(settingsSource);
checkHaRoleOverrideSelectpicker(settingsSource);

console.log('HA_NOTICE_KEYBOARD=PASS native-button');
console.log('HA_NOTICE_EXPANSION=PASS states=2');
console.log('HA_NOTICE_REFRESH_PRESERVES_EXPANSION=PASS');
console.log('HA_RELEVANCE_CONTROLS=PASS');
console.log('HA_ROLE_SELECTPICKER=PASS init=explicit refresh=async+state open=space+enter focus=plugin-proxy submit=no');
console.log('HA_VISIBILITY_DEVICES_SETTINGS_CONSISTENT=PASS');
console.log('HA_VISIBILITY_REFRESH_FAILURE=PASS');
console.log('HA_VISIBILITY_NO_APPLY_REFRESH=PASS');
console.log('HA_ROLE_VISIBILITY_JS=PASS cases=' + count);
