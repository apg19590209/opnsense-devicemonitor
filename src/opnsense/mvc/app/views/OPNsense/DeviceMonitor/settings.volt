<div class="content-box">
    <div class="content-box-main">

        <h1 style="padding-left:10px;">
            {{ lang._('Device Monitor') }}
            <small id="settings-version" style="font-size:13px;color:#888;margin-left:5px;"></small>
            <span style="color:#555;margin:0 8px;">–</span>
            <span style="font-weight:normal;font-size:18px;">{{ lang._('Settings') }}</span>
        </h1>

        <ul class="nav nav-tabs" role="tablist" style="margin:10px 0 0 0;">
            <li role="presentation" class="active">
                <a href="#tab-monitoring" role="tab" data-toggle="tab">
                    <i class="fa fa-desktop"></i> {{ lang._('Monitoring') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-nmap" role="tab" data-toggle="tab">
                    <i class="fa fa-search"></i> {{ lang._('Nmap Scanning') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-email" role="tab" data-toggle="tab">
                    <i class="fa fa-envelope-o"></i> {{ lang._('Email Notifications') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-webhook" role="tab" data-toggle="tab">
                    <i class="fa fa-bell-o"></i> {{ lang._('Webhook Notifications') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-about" role="tab" data-toggle="tab">
                    <i class="fa fa-info-circle"></i> {{ lang._('About') }}
                </a>
            </li>
        </ul>

        <div class="tab-content" style="padding:15px 0;">

            <!-- TAB 3: Email -->
            <div role="tabpanel" class="tab-pane" id="tab-email">
                <div class="alert alert-info">
                    {{ lang._('Configure email notifications for new devices on the network') }}
                </div>
                <table class="table table-striped">
                    <tbody>
                        <tr>
                            <td style="width:30%;vertical-align:top;">
                                <label>
                                    <input type="checkbox" id="email_enabled" />
                                    <strong>{{ lang._('Enable Email') }}</strong>
                                </label>
                            </td>
                            <td>
                                <div id="email_config">

                                    <label>{{ lang._('Email Recipient') }}:</label>
                                    <input type="email" id="email_to" class="form-control" placeholder="admin@example.com" style="max-width:400px;" />
                                    <small class="text-muted">{{ lang._('Where to send notifications') }}</small>
                                    <br><br>

                                    <label>{{ lang._('Email Sender') }}:</label>
                                    <input type="email" id="email_from" class="form-control" placeholder="devicemonitor@opnsense.local" style="max-width:400px;" />
                                    <small class="text-muted">{{ lang._('From address') }}</small>
                                    <br><br>

                                    <label>{{ lang._('Email delivery method') }}:</label>
                                    <select id="email_method" class="form-control" style="max-width:400px;">
                                        <option value="sendmail">{{ lang._('Local Sendmail / Postfix') }}</option>
                                        <option value="smtp">{{ lang._('Direct SMTP (built into Device Monitor)') }}</option>
                                    </select>
                                    <small class="text-muted">{{ lang._('Choose the mail transport that matches your OPNsense installation') }}</small>

                                    <div id="email_sendmail_config" class="alert alert-info" style="margin-top:12px;max-width:600px;">
                                        <strong>{{ lang._('Local Sendmail / Postfix') }}</strong><br>
                                        {{ lang._('Uses /usr/local/sbin/sendmail. This is suitable when a local mailer such as the os-postfix plugin is installed and configured.') }}
                                    </div>

                                    <div id="email_smtp_config" style="margin-top:14px;max-width:600px;display:none;">
                                        <div class="alert alert-info">
                                            {{ lang._('Direct SMTP uses the Python standard library and does not require Postfix, sendmail or Monit.') }}
                                        </div>

                                        <label>{{ lang._('SMTP Server') }}:</label>
                                        <input type="text" id="smtp_host" class="form-control" placeholder="smtp.example.com" style="max-width:400px;" />
                                        <br>

                                        <div style="display:flex;gap:15px;align-items:flex-end;flex-wrap:wrap;">
                                            <div>
                                                <label>{{ lang._('SMTP Port') }}:</label>
                                                <input type="number" id="smtp_port" class="form-control" value="587" min="1" max="65535" style="width:120px;" />
                                            </div>
                                            <div>
                                                <label>{{ lang._('Encryption') }}:</label>
                                                <select id="smtp_encryption" class="form-control" style="width:180px;">
                                                    <option value="starttls">STARTTLS</option>
                                                    <option value="ssl">SSL/TLS</option>
                                                    <option value="none">{{ lang._('None') }}</option>
                                                </select>
                                            </div>
                                        </div>
                                        <br>

                                        <label>{{ lang._('SMTP Username') }}:</label>
                                        <input type="text" id="smtp_username" class="form-control" autocomplete="username" style="max-width:400px;" />
                                        <small class="text-muted">{{ lang._('Leave empty if the SMTP server does not require authentication') }}</small>
                                        <br><br>

                                        <label>{{ lang._('SMTP Password') }}:</label>
                                        <input type="password" id="smtp_password" class="form-control" autocomplete="new-password" style="max-width:400px;" />
                                    </div>

                                    <button type="button" id="btn-test-email" class="btn btn-default btn-sm" style="margin-top:14px;">
                                        🧪 {{ lang._('Test Email') }}
                                    </button>
                                    <small class="text-muted" style="margin-left:8px;">{{ lang._('The current email settings are saved before the test is sent') }}</small>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="vertical-align:top;padding-top:16px;">
                                <strong>{{ lang._('IP & MAC Conflicts') }}</strong>
                            </td>
                            <td style="padding-top:16px;">
                                <label style="margin:0;">
                                    <input type="checkbox" id="identity_email_enabled" />
                                    <strong>{{ lang._('Email high-severity conflict alerts') }}</strong>
                                </label>
                                <br>
                                <small class="text-muted">{{ lang._('Send an email when a new high-severity IPv4 or IPv6 address conflict is detected.') }}</small>
                            </td>
                        </tr>
                        <tr>
                            <td style="vertical-align:top;padding-top:16px;">
                                <strong>{{ lang._('Notify for interfaces') }}</strong>
                            </td>
                            <td>
                                <small class="text-muted">{{ lang._('Leave empty to receive notifications from all interfaces') }}</small>
                                <div style="margin-top:6px;border:1px solid #444;border-radius:4px;padding:8px;max-width:350px;max-height:180px;overflow-y:auto;" id="email-vlan-list"></div>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div style="padding:10px 0 0 0;">
                    <button type="button" class="btn btn-primary btn-apply" id="btn-apply-email">
                        <i class="fa fa-check"></i> {{ lang._('Apply') }}
                    </button>
                </div>
            </div>

            <!-- TAB 4: Webhook -->
            <div role="tabpanel" class="tab-pane" id="tab-webhook">
                <div class="alert alert-info">
                    {{ lang._('Configure webhook notifications for new devices on the network') }}
                </div>
                <table class="table table-striped">
                    <tbody>
                        <tr>
                            <td style="width:30%;vertical-align:top;">
                                <label>
                                    <input type="checkbox" id="webhook_enabled" />
                                    <strong>{{ lang._('Enable Webhook') }}</strong>
                                </label>
                            </td>
                            <td>
                                <div id="webhook_config">
                                    <label>{{ lang._('Webhook URL') }}:</label>
                                    <input type="text" id="webhook_url" class="form-control" placeholder="https://ntfy.sh/your_topic" style="max-width:500px;" />
                                    <div style="margin-top:10px;padding:12px;background:#f8f9fa;border-left:4px solid #007bff;border-radius:4px;max-width:500px;">
                                        <div style="font-weight:600;color:#495057;margin-bottom:8px;">💡 Examples:</div>
                                        <div style="display:flex;flex-direction:column;gap:6px;">
                                            <div><span style="display:inline-block;background:#e3f2fd;color:#1976d2;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:8px;">ntfy.sh</span><code>https://ntfy.sh/opnsense_monitor</code></div>
                                            <div><span style="display:inline-block;background:#ede7f6;color:#5e35b1;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:8px;">Discord</span><code>https://discord.com/api/webhooks/...</code></div>
                                            <div><span style="display:inline-block;background:#e8f5e9;color:#388e3c;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:8px;">Custom</span><code>https://your-server.com/webhook</code></div>
                                        </div>
                                    </div>
                                    <br>
                                    <button type="button" id="test_webhook" class="btn btn-default btn-sm">
                                        🧪 {{ lang._('Send Test') }}
                                    </button>
                                    <span id="webhook_test_result" style="margin-left:10px;font-weight:bold;"></span>
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td style="vertical-align:top;padding-top:16px;">
                                <strong>{{ lang._('Notify for interfaces') }}</strong>
                            </td>
                            <td>
                                <small class="text-muted">{{ lang._('Leave empty to receive notifications from all interfaces') }}</small>
                                <div style="margin-top:6px;border:1px solid #444;border-radius:4px;padding:8px;max-width:350px;max-height:180px;overflow-y:auto;" id="webhook-vlan-list"></div>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div style="padding:10px 0 0 0;">
                    <button type="button" class="btn btn-primary btn-apply" id="btn-apply-webhook">
                        <i class="fa fa-check"></i> {{ lang._('Apply') }}
                    </button>
                </div>
            </div>

            <!-- TAB 1: Monitoring -->
            <div role="tabpanel" class="tab-pane active" id="tab-monitoring">
                <table class="table table-striped">
                    <tbody>
                        <tr>
                            <td style="width:30%;"><strong>{{ lang._('Enable Monitoring') }}</strong></td>
                            <td>
                                <input type="checkbox" id="enabled" />
                                <small class="text-muted" style="margin-left:8px;">{{ lang._('Enable automatic network monitoring') }}</small>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>{{ lang._('Scan Interval') }}</strong></td>
                            <td>
                                <div style="display:flex;align-items:center;gap:10px;">
                                    <input type="number" id="scan_interval" class="form-control" value="300" min="60" max="3600" style="max-width:120px;" />
                                    <span class="text-muted">{{ lang._('seconds') }}</span>
                                </div>
                                <small class="text-muted">{{ lang._('Seconds between scans (60-3600)') }}</small>
                            </td>
                        </tr>

                    </tbody>
                </table>

                <div style="padding:10px 0 0 0;">
                    <button type="button"
                            class="btn btn-primary btn-apply"
                            id="btn-apply-monitoring">
                        <i class="fa fa-check"></i> {{ lang._('Apply') }}
                    </button>
                </div>
            </div>

            <!-- TAB 2: Nmap Scanning -->
            <div role="tabpanel" class="tab-pane" id="tab-nmap">
                <table class="table table-striped">
                    <tbody>
                        <tr>
                            <td colspan="2">
                                <h4 style="margin:5px 0;">{{ lang._('Targeted Nmap Scanning') }}</h4>
                                <small class="text-muted">{{ lang._('Optional detailed scan performed for newly detected devices after notification.') }}</small>
                            </td>
                        </tr>

                        <tr>
                            <td><strong>{{ lang._('Enable Targeted Nmap') }}</strong></td>
                            <td>
                                <input type="checkbox" id="targeted_nmap_enabled" />
                                <small class="text-muted" style="margin-left:8px;">{{ lang._('Automatically scan newly detected devices') }}</small>
                            </td>
                        </tr>

                        <tr>
                            <td><strong>{{ lang._('Top TCP Ports') }}</strong></td>
                            <td>
                                <input type="number" id="nmap_top_ports" class="form-control" value="100" min="1" max="1000" style="max-width:120px;" />
                                <small class="text-muted">{{ lang._('Number of most common TCP ports to scan (1-1000)') }}</small>
                            </td>
                        </tr>

                        <tr>
                            <td><strong>{{ lang._('Timing Template') }}</strong></td>
                            <td>
                                <select id="nmap_timing" class="form-control" style="max-width:180px;">
                                    <option value="0">T0</option>
                                    <option value="1">T1</option>
                                    <option value="2">T2</option>
                                    <option value="3">T3</option>
                                    <option value="4">T4</option>
                                    <option value="5">T5</option>
                                </select>
                                <small class="text-muted">{{ lang._('Nmap timing template. T4 is the default.') }}</small>
                            </td>
                        </tr>

                        <tr>
                            <td><strong>{{ lang._('Host Timeout') }}</strong></td>
                            <td>
                                <div style="display:flex;align-items:center;gap:10px;">
                                    <input type="number" id="nmap_host_timeout" class="form-control" value="45" min="10" max="300" style="max-width:120px;" />
                                    <span class="text-muted">{{ lang._('seconds') }}</span>
                                </div>
                                <small class="text-muted">{{ lang._('Maximum Nmap scan time per device (10-300 seconds)') }}</small>
                            </td>
                        </tr>

                        <tr>
                            <td><strong>{{ lang._('Version Detection') }}</strong></td>
                            <td>
                                <input type="checkbox" id="nmap_version_detection" />
                                <small class="text-muted" style="margin-left:8px;">{{ lang._('Detect services and versions using light detection') }}</small>
                            </td>
                        </tr>

                        <tr>
                            <td><strong>{{ lang._('Maximum Scans Per Cycle') }}</strong></td>
                            <td>
                                <input type="number" id="nmap_max_per_cycle" class="form-control" value="2" min="1" max="10" style="max-width:120px;" />
                                <small class="text-muted">{{ lang._('Maximum queued targeted scans processed during one monitoring cycle (1-10)') }}</small>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div style="padding:10px 0 0 0;">
                    <button type="button" class="btn btn-primary btn-apply" id="btn-apply-nmap">
                        <i class="fa fa-check"></i> {{ lang._('Apply') }}
                    </button>
                </div>
            </div>

            <!-- TAB 5: About -->
            <div role="tabpanel" class="tab-pane" id="tab-about">
                <div style="max-width:600px;padding:10px 0;">
                    <h3 style="margin-top:0;">{{ lang._('Device Monitor') }} <span id="about-version" style="color:#888;font-size:16px;"></span></h3>
                    <p class="text-muted">{{ lang._('OPNsense plugin for monitoring network devices using the native hostwatch database.') }}</p>
                    <table class="table table-condensed" style="margin-top:20px;">
                        <tr>
                            <th colspan="2" style="padding-top:14px;">{{ lang._('Original Project') }}</th>
                        </tr>
                        <tr>
                            <td style="width:40%;color:#888;">{{ lang._('Creator') }}</td>
                            <td>Hacesoft</td>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ lang._('Repository') }}</td>
                            <td><a href="https://github.com/hacesoft/opnsense-devicemonitor" target="_blank">github.com/hacesoft/opnsense-devicemonitor</a></td>
                        </tr>

                        <tr>
                            <th colspan="2" style="padding-top:18px;">{{ lang._('v2.7 Development & Enhancements') }}</th>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ lang._('Developer') }}</td>
                            <td>Anthony Gonzalez</td>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ lang._('Repository') }}</td>
                            <td><a href="https://github.com/apg19590209/opnsense-devicemonitor" target="_blank">github.com/apg19590209/opnsense-devicemonitor</a></td>
                        </tr>
                        <tr>
                            <th colspan="2" style="padding-top:18px;">{{ lang._('Licensing & Compatibility') }}</th>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ lang._('License') }}</td>
                            <td>MIT</td>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ lang._('Requires OPNsense') }}</td>
                            <td>&ge; 26.1.5</td>
                        </tr>
                    </table>
                </div>
            </div>

        </div>
    </div>
</div>

<script>
$().ready(function() {
    var translations = {
        config_saved:  '{{ lang._('Configuration saved') }}',
        config_error:  '{{ lang._('Error saving configuration') }}',
        test_sent:     '{{ lang._('Test email sent to') }}',
        test_failed:   '{{ lang._('Failed to send email') }}',
        saving:        '{{ lang._('Saving...') }}'
    };

    var allVlanNames = {};

    function showToast(msg, type) {
        var bg = type==='success'?'#4CAF50':(type==='error'?'#f44336':'#2196F3');
        var ic = type==='success'?'fa-check-circle':(type==='error'?'fa-exclamation-circle':'fa-info-circle');
        var $t = $('<div>').css({position:'fixed',top:'20px',right:'20px','background-color':bg,color:'white',
            padding:'15px 20px','border-radius':'4px','box-shadow':'0 4px 8px rgba(0,0,0,.3)',
            'z-index':9999,'min-width':'280px',display:'none'})
            .html('<i class="fa '+ic+'"></i> '+msg);
        $('body').append($t); $t.fadeIn(300);
        setTimeout(function(){ $t.fadeOut(300,function(){ $t.remove(); }); },3000);
    }

    // Version
    $.getJSON('/api/devicemonitor/config/getversion', function(d) {
        var v = 'v'+(d.version||'?');
        $('#settings-version').text(v);
        $('#about-version').text(v);
    });

    // Build VLAN checklist in a container
    function buildVlanCheckList(containerId, selectedVlans) {
        var $c = $('#'+containerId).empty();
        var vlans = Object.keys(allVlanNames).sort();
        if (!vlans.length) {
            $c.html('<em style="color:#888;font-size:12px;">{{ lang._('No interfaces found') }}</em>');
            return;
        }
        var sel = selectedVlans ? selectedVlans.split(',').map(function(v){return v.trim();}).filter(Boolean) : [];
        vlans.forEach(function(v) {
            var n = allVlanNames[v];
            var label = (n && n !== v) ? v+' \u2013 '+n : v;
            var chk = (sel.length === 0) || (sel.indexOf(v) !== -1);
            $c.append($('<label>').css({display:'block',margin:'3px 0',fontWeight:'normal',cursor:'pointer'}).append(
                $('<input type="checkbox" class="notif-vlan-cb">').val(v).prop('checked',chk),
                $('<span>').css('margin-left','8px').text(label)
            ));
        });
    }

    function getSelectedVlans(containerId) {
        var sel=[], total=$('#'+containerId+' .notif-vlan-cb').length;
        $('#'+containerId+' .notif-vlan-cb:checked').each(function(){ sel.push($(this).val()); });
        return (sel.length===total) ? '' : sel.join(',');
    }

    function loadConfig() {
        $.ajax({ url:'/api/devicemonitor/config/get', type:'GET', success:function(d) {
            $('#enabled').prop('checked', d.enabled==='1');
            $('#scan_interval').val(d.scan_interval||300);
            $('#targeted_nmap_enabled').prop(
                'checked',
                String(
                    d.targeted_nmap_enabled !== undefined &&
                    d.targeted_nmap_enabled !== null
                        ? d.targeted_nmap_enabled
                        : '1'
                ) === '1'
            );
            $('#nmap_top_ports').val(d.nmap_top_ports||100);
            $('#nmap_timing').val(
                d.nmap_timing !== undefined &&
                d.nmap_timing !== null
                    ? d.nmap_timing
                    : 4
            );
            $('#nmap_host_timeout').val(d.nmap_host_timeout||45);
            $('#nmap_version_detection').prop(
                'checked',
                String(
                    d.nmap_version_detection !== undefined &&
                    d.nmap_version_detection !== null
                        ? d.nmap_version_detection
                        : '1'
                ) === '1'
            );
            $('#nmap_max_per_cycle').val(d.nmap_max_per_cycle||2);
            $('#email_enabled').prop('checked', d.email_enabled==='1');
            $('#identity_email_enabled').prop('checked', d.identity_email_enabled==='1');
            $('#email_to').val(d.email_to||'');
            $('#email_from').val(d.email_from||'devicemonitor@opnsense.local');
            $('#email_method').val(d.email_method||'sendmail');
            $('#smtp_host').val(d.smtp_host||'');
            $('#smtp_port').val(d.smtp_port||587);
            $('#smtp_encryption').val(d.smtp_encryption||'starttls');
            $('#smtp_username').val(d.smtp_username||'');
            $('#smtp_password').val(d.smtp_password||'');
            $('#webhook_enabled').prop('checked', d.webhook_enabled==='1');
            $('#webhook_url').val(d.webhook_url||'');
            buildVlanCheckList('email-vlan-list',   d.email_vlans   || '');
            buildVlanCheckList('webhook-vlan-list', d.webhook_vlans || '');
            toggleEmailConfig();
            toggleEmailMethod();
            toggleWebhookConfig();
        }});
    }

    function toggleEmailConfig() {
        $('#email_enabled').prop('checked') ? $('#email_config').slideDown() : $('#email_config').slideUp();
    }
    function toggleEmailMethod() {
        var method = $('#email_method').val() || 'sendmail';
        if (method === 'smtp') {
            $('#email_sendmail_config').hide();
            $('#email_smtp_config').show();
        } else {
            $('#email_smtp_config').hide();
            $('#email_sendmail_config').show();
        }
    }
    function toggleWebhookConfig() {
        $('#webhook_enabled').prop('checked') ? $('#webhook_config').slideDown() : $('#webhook_config').slideUp();
    }
    $('#email_enabled').change(toggleEmailConfig);
    $('#email_method').change(toggleEmailMethod);
    $('#webhook_enabled').change(toggleWebhookConfig);

    function collectConfigData() {
        return {
            enabled:          $('#enabled').is(':checked')?'1':'0',
            email_enabled:    $('#email_enabled').is(':checked')?'1':'0',
            identity_email_enabled: $('#identity_email_enabled').is(':checked')?'1':'0',
            email_to:         $('#email_to').val(),
            email_from:       $('#email_from').val(),
            email_method:     $('#email_method').val(),
            smtp_host:        $('#smtp_host').val(),
            smtp_port:        $('#smtp_port').val(),
            smtp_encryption:  $('#smtp_encryption').val(),
            smtp_username:    $('#smtp_username').val(),
            smtp_password:    $('#smtp_password').val(),
            email_vlans:      getSelectedVlans('email-vlan-list'),
            webhook_enabled:  $('#webhook_enabled').is(':checked')?'1':'0',
            webhook_url:      $('#webhook_url').val(),
            webhook_vlans:    getSelectedVlans('webhook-vlan-list'),
            scan_interval: $('#scan_interval').val(),
            targeted_nmap_enabled: $('#targeted_nmap_enabled').is(':checked')?'1':'0',
            nmap_top_ports: $('#nmap_top_ports').val(),
            nmap_timing: $('#nmap_timing').val(),
            nmap_host_timeout: $('#nmap_host_timeout').val(),
            nmap_version_detection: $('#nmap_version_detection').is(':checked')?'1':'0',
            nmap_max_per_cycle: $('#nmap_max_per_cycle').val()
        };
    }

    function saveConfig($btn, onSuccess) {
        var orig = $btn.html();
        $btn.prop('disabled',true).html('<i class="fa fa-spinner fa-spin"></i> '+translations.saving);
        $.ajax({ url:'/api/devicemonitor/config/set', type:'POST', data:collectConfigData(), success:function(r) {
            $btn.prop('disabled',false).html(orig);
            if (r.result==='saved') {
                if (typeof onSuccess === 'function') {
                    onSuccess();
                } else {
                    showToast(translations.config_saved,'success');
                }
            } else {
                showToast(r.message||translations.config_error,'error');
            }
        }, error:function() {
            $btn.prop('disabled',false).html(orig);
            showToast(translations.config_error,'error');
        }});
    }

    $('.btn-apply').click(function(){ saveConfig($(this)); });

    $('#btn-test-email').click(function() {
        var email=$('#email_to').val();
        if (!email) { showToast('{{ lang._('Please enter recipient email first') }}','error'); return; }
        var $b=$(this), orig=$b.html();

        // Save the current form first so the test always uses the selected
        // transport and the values currently visible in the UI.
        saveConfig($b, function() {
            $b.prop('disabled',true).html('<i class="fa fa-spinner fa-spin"></i>');
            $.ajax({ url:'/api/devicemonitor/config/testemail', type:'POST', success:function(r) {
                $b.prop('disabled',false).html(orig);
                var transport = r.transport ? ' ('+r.transport+')' : '';
                showToast(r.result==='sent'?translations.test_sent+' '+email+transport:(r.message||translations.test_failed),
                          r.result==='sent'?'success':'error');
            }, error:function() {
                $b.prop('disabled',false).html(orig);
                showToast(translations.test_failed,'error');
            }});
        });
    });

    $('#test_webhook').click(function() {
        var url=$('#webhook_url').val();
        if (!url) { $('#webhook_test_result').html('<span style="color:red;">❌ {{ lang._('Enter webhook URL first') }}</span>'); return; }
        $('#webhook_test_result').html('<span style="color:blue;">⏳ {{ lang._('Sending...') }}</span>');
        $.ajax({ url:'/api/devicemonitor/config/testWebhook', type:'POST', data:{webhook_url:url},
            success:function(d) {
                $('#webhook_test_result').html(d.result==='ok'
                    ? '<span style="color:green;">✅ {{ lang._('Test sent!') }}</span>'
                    : '<span style="color:red;">❌ '+(d.message||'{{ lang._('Failed') }}')+'</span>');
            }
        });
    });

    // Load interfaces then config
    $.ajax({ url:'/api/devicemonitor/config/getinterfaces', type:'GET',
        success:function(data){ allVlanNames=data||{}; loadConfig(); },
        error:function(){ loadConfig(); }
    });
});
</script>
