<div class="content-box">
    <div class="content-box-main">

        <ul class="nav nav-tabs dm-settings-tabs" role="tablist">
            <li role="presentation" class="active">
                <a href="#tab-monitoring" role="tab" data-toggle="tab" aria-controls="tab-monitoring" aria-selected="true">
                    <i class="fa fa-desktop" aria-hidden="true"></i> {{ devicemonitor_t('Monitoring') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-nmap" role="tab" data-toggle="tab" aria-controls="tab-nmap" aria-selected="false">
                    <i class="fa fa-search" aria-hidden="true"></i> {{ devicemonitor_t('Nmap Scanning') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-email" role="tab" data-toggle="tab" aria-controls="tab-email" aria-selected="false">
                    <i class="fa fa-envelope-o" aria-hidden="true"></i> {{ devicemonitor_t('Email Notifications') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-webhook" role="tab" data-toggle="tab" aria-controls="tab-webhook" aria-selected="false">
                    <i class="fa fa-bell-o" aria-hidden="true"></i> {{ devicemonitor_t('Webhook Notifications') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-pluginoptions" role="tab" data-toggle="tab" aria-controls="tab-pluginoptions" aria-selected="false">
                    <i class="fa fa-cog" aria-hidden="true"></i> {{ devicemonitor_t('Plugin Options') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-ha" role="tab" data-toggle="tab" aria-controls="tab-ha" aria-selected="false">
                    <i class="fa fa-clone" aria-hidden="true"></i> {{ devicemonitor_t('HA / CARP') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-peers" role="tab" data-toggle="tab" aria-controls="tab-peers" aria-selected="false">
                    <i class="fa fa-exchange" aria-hidden="true"></i> {{ devicemonitor_t('Email Log Peers') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-about" role="tab" data-toggle="tab" aria-controls="tab-about" aria-selected="false">
                    <i class="fa fa-info-circle" aria-hidden="true"></i> {{ devicemonitor_t('About') }}
                </a>
            </li>
        </ul>

        <!-- Persistent and shared in meaning with Devices: the settings below
             are local to this node, and BACKUP suppression must be visible even
             when the HA / CARP tab is not open. -->
        <div id="dm-ha-node-notice" class="alert alert-info dm-ha-node-notice" role="status" aria-live="polite">
            <span class="sr-only">{{ devicemonitor_t('Node-local Device Monitor data') }}</span>
            <div class="dm-ha-node-notice-head">
                <div id="dm-ha-node-summary" class="dm-ha-node-summary"></div>
                <button type="button" id="dm-ha-node-toggle"
                        class="btn btn-default btn-xs dm-ha-node-toggle"
                        aria-expanded="false" aria-controls="dm-ha-node-details">
                    <span id="dm-ha-node-toggle-label">{{ devicemonitor_t('Show details') }}</span>
                    <span class="caret" aria-hidden="true"></span>
                </button>
            </div>
            <div id="dm-ha-node-summary-warning" class="dm-ha-node-summary-warning" style="display:none;"></div>
            <div id="dm-ha-node-details" class="dm-ha-node-details" hidden>
                <div id="dm-ha-node-role-facts" class="dm-ha-node-role-facts">
                    <span>{{ devicemonitor_t('Detected role') }}: <strong id="dm-ha-node-role"></strong></span>
                    <span>{{ devicemonitor_t('Effective mode') }}: <strong id="dm-ha-node-mode"></strong></span>
                </div>
                <div id="dm-ha-node-ownership" class="dm-ha-node-ownership"></div>
                <div id="dm-ha-node-activity-details" class="dm-ha-node-activity-details">
                    <div id="dm-ha-node-paused-block" style="display:none;">
                        <strong id="dm-ha-node-paused-heading"></strong>
                        <ul id="dm-ha-node-paused" class="dm-ha-node-paused-list"></ul>
                        <div id="dm-ha-node-paused-note"></div>
                    </div>
                    <div id="dm-ha-node-continuing-block" class="dm-ha-node-continuing-block">
                        <strong id="dm-ha-node-continuing-heading"></strong>
                        <div id="dm-ha-node-continuation"></div>
                    </div>
                </div>
                <div id="dm-ha-node-last-scan" class="dm-ha-node-last-scan"></div>
            </div>
        </div>

        <!-- Panes are addressed by id, not by position: the DOM order below is
             Monitoring, Nmap, Email, Webhook, Plugin Options, HA/CARP and About,
             which matches the tab order above. `active` must sit on exactly one
             pane and on the matching list item, otherwise the first paint shows a
             blank panel. -->
        <div class="tab-content dm-settings-panes">

            <!-- TAB 1: Monitoring -->
            <div role="tabpanel" class="tab-pane active" id="tab-monitoring">
                <form class="dm-pane-form">
                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Enable Monitoring') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Enable Monitoring') }}" data-content="{{ devicemonitor_t('Enable automatic network monitoring') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <input type="checkbox" id="enabled" />
                    </div>
                </div>
                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Monitored Interfaces') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Monitored Interfaces') }}" data-content="{{ devicemonitor_t('Only devices on selected interfaces are scanned. With no selection, scanning is refused.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <div style="margin-top:6px;border:1px solid #444;border-radius:4px;padding:8px;max-width:450px;max-height:200px;overflow-y:auto;" id="monitored-interface-list"></div>
                        <div id="monitored-interface-warning" class="text-danger" style="margin-top:6px;display:none;">
                            <i class="fa fa-exclamation-triangle"></i> {{ devicemonitor_t('Monitoring is enabled but no interface is selected. Scans will be refused.') }}
                        </div>
                    </div>
                </div>
                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Scan Interval') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Scan Interval') }}" data-content="{{ devicemonitor_t('Seconds between scans (60-3600)') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <div style="display:flex;align-items:center;gap:10px;">
                            <input type="number" id="scan_interval" class="form-control" value="300" min="60" max="3600" style="max-width:120px;" />
                            <span class="text-muted">{{ devicemonitor_t('seconds') }}</span>
                        </div>
                    </div>
                </div>

                <div style="padding:10px 0 0 0;">
                    <button type="button"
                            class="btn btn-primary btn-apply"
                            id="btn-apply-monitoring">
                        <i class="fa fa-check"></i> {{ devicemonitor_t('Apply') }}
                    </button>
                </div>
                </form>
            </div>

            <!-- TAB 2: Nmap Scanning -->
            <div role="tabpanel" class="tab-pane" id="tab-nmap">
                <form class="dm-pane-form">
                <div class="row form-group">
                    <div class="col-xs-12 col-md-3">
                        <h4 style="margin:5px 0;">{{ devicemonitor_t('Targeted Nmap Scanning') }} <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Targeted Nmap Scanning') }}" data-content="{{ devicemonitor_t('Optional detailed scan performed for newly detected devices after notification.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button></h4>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Enable Targeted Nmap') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Enable Targeted Nmap') }}" data-content="{{ devicemonitor_t('Automatically scan newly detected devices') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <input type="checkbox" id="targeted_nmap_enabled" />
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Top TCP Ports') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Top TCP Ports') }}" data-content="{{ devicemonitor_t('Number of most common TCP ports to scan (1-1000)') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <input type="number" id="nmap_top_ports" class="form-control" value="100" min="1" max="1000" style="max-width:120px;" />
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Timing Template') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Timing Template') }}" data-content="{{ devicemonitor_t('Nmap timing template. T4 is the default.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <select id="nmap_timing" class="selectpicker" data-style="btn-default" data-width="180px">
                            <option value="0">T0</option>
                            <option value="1">T1</option>
                            <option value="2">T2</option>
                            <option value="3">T3</option>
                            <option value="4">T4</option>
                            <option value="5">T5</option>
                        </select>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Host Timeout') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Host Timeout') }}" data-content="{{ devicemonitor_t('Maximum Nmap scan time per device (10-300 seconds)') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <div style="display:flex;align-items:center;gap:10px;">
                            <input type="number" id="nmap_host_timeout" class="form-control" value="45" min="10" max="300" style="max-width:120px;" />
                            <span class="text-muted">{{ devicemonitor_t('seconds') }}</span>
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Version Detection') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Version Detection') }}" data-content="{{ devicemonitor_t('Detect services and versions using light detection') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <input type="checkbox" id="nmap_version_detection" />
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Maximum Scans Per Cycle') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Maximum Scans Per Cycle') }}" data-content="{{ devicemonitor_t('Maximum queued targeted scans processed during one monitoring cycle (1-10)') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <input type="number" id="nmap_max_per_cycle" class="form-control" value="2" min="1" max="10" style="max-width:120px;" />
                    </div>
                </div>
                <div style="padding:10px 0 0 0;">
                    <button type="button" class="btn btn-primary btn-apply" id="btn-apply-nmap">
                        <i class="fa fa-check"></i> {{ devicemonitor_t('Apply') }}
                    </button>
                </div>
                </form>
            </div>

            <!-- TAB 3: Email -->
            <div role="tabpanel" class="tab-pane" id="tab-email">
                <form class="dm-pane-form">
                <a id="return-to-device-details" class="btn btn-default btn-sm"
                   href="#" style="display:none;margin-bottom:12px;">
                    <i class="fa fa-arrow-left" aria-hidden="true"></i>
                    {{ devicemonitor_t('Back to Network Identity Details') }}
                </a>
                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Email Notifications') }}</strong>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="email_enabled" />
                            <strong>{{ devicemonitor_t('Enable Email') }}</strong>
                        </label>
                    </div>
                </div>

                <div id="email_config">
                    <div class="row form-group">
                        <div class="col-md-3">
                            <label>{{ devicemonitor_t('Repeat unchanged alerts') }}:</label>
                        </div>
                        <div class="col-md-9">
                            <p class="help-block" style="margin-top:0;">
                                {{ devicemonitor_t('Emails are sent when the state changes. Set how often each category is repeated while the state has not changed. 0 never repeats.') }}
                            </p>
                            <datalist id="reminder-minute-options">
                                <option value="5"></option>
                                <option value="10"></option>
                                <option value="15"></option>
                                <option value="30"></option>
                                <option value="45"></option>
                                <option value="60"></option>
                            </datalist>

                            <div class="form-inline" style="margin-bottom:6px;">
                                <label for="email_reminder_scan" style="min-width:150px;font-weight:normal;">
                                    {{ devicemonitor_t('Scan results') }}
                                </label>
                                <input type="number" id="email_reminder_scan" class="form-control"
                                       list="reminder-minute-options" min="0" max="1440" step="1"
                                       value="0" style="max-width:100px;" />
                                <span class="help-block" style="display:inline;margin-left:6px;">
                                    {{ devicemonitor_t('minutes') }}
                                </span>
                            </div>

                            <div class="form-inline" style="margin-bottom:6px;">
                                <label for="email_reminder_service" style="min-width:150px;font-weight:normal;">
                                    {{ devicemonitor_t('Service outages') }}
                                </label>
                                <input type="number" id="email_reminder_service" class="form-control"
                                       list="reminder-minute-options" min="0" max="1440" step="1"
                                       value="0" style="max-width:100px;" />
                                <span class="help-block" style="display:inline;margin-left:6px;">
                                    {{ devicemonitor_t('minutes') }}
                                </span>
                            </div>

                            <div class="form-inline" style="margin-bottom:6px;">
                                <label for="email_reminder_identity" style="min-width:150px;font-weight:normal;">
                                    {{ devicemonitor_t('Identity conflicts') }}
                                </label>
                                <input type="number" id="email_reminder_identity" class="form-control"
                                       list="reminder-minute-options" min="0" max="1440" step="1"
                                       value="0" style="max-width:100px;" />
                                <span class="help-block" style="display:inline;margin-left:6px;">
                                    {{ devicemonitor_t('minutes') }}
                                </span>
                            </div>

                            <div class="form-inline" style="margin-bottom:6px;">
                                <label for="email_reminder_new_device" style="min-width:150px;font-weight:normal;">
                                    {{ devicemonitor_t('MAC change announcements') }}
                                </label>
                                <input type="number" id="email_reminder_new_device" class="form-control"
                                       list="reminder-minute-options" min="0" max="1440" step="1"
                                       value="0" style="max-width:100px;" />
                                <span class="help-block" style="display:inline;margin-left:6px;">
                                    {{ devicemonitor_t('minutes') }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="row form-group">
                        <div class="col-md-3">
                            <label>{{ devicemonitor_t('Email Recipient') }}:</label>
                        </div>
                        <div class="col-md-9">
                            <input type="email" id="email_to" class="form-control" placeholder="admin@example.com" style="max-width:400px;" />
                        </div>
                    </div>

                    <div class="row form-group">
                        <div class="col-md-3">
                            <label>{{ devicemonitor_t('Email Sender') }}:</label>
                        </div>
                        <div class="col-md-9">
                            <input type="email" id="email_from" class="form-control" placeholder="devicemonitor@opnsense.local" style="max-width:400px;" />
                        </div>
                    </div>

                    <div class="row form-group">
                        <div class="col-md-3">
                            <label>{{ devicemonitor_t('Email delivery method') }}:</label>
                            <button type="button" id="email_sendmail_config" class="dm-info" aria-label="{{ devicemonitor_t('About Email Delivery') }}"
                                    data-content="{{ devicemonitor_t('Choose the mail transport that matches your OPNsense installation') }} {{ devicemonitor_t('Uses /usr/local/sbin/sendmail. This is suitable when a local mailer such as the os-postfix plugin is installed and configured.') }}">
                                <i class="fa fa-info-circle" aria-hidden="true"></i>
                            </button>
                        </div>
                        <div class="col-md-9">
                            <select id="email_method" class="selectpicker" data-style="btn-default" data-width="400px">
                                <option value="sendmail">{{ devicemonitor_t('Local Sendmail / Postfix') }}</option>
                                <option value="smtp">{{ devicemonitor_t('Direct SMTP (built into Device Monitor)') }}</option>
                            </select>
                        </div>
                    </div>

                    <div id="email_smtp_config" style="margin-top:14px;display:none;">
                        <div class="row form-group">
                            <div class="col-xs-12 col-md-3">
                                <label>{{ devicemonitor_t('SMTP Server') }}:</label>
                                <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Direct SMTP') }}"
                                        data-content="{{ devicemonitor_t('Direct SMTP uses the Python standard library and does not require Postfix, sendmail or Monit.') }}">
                                    <i class="fa fa-info-circle" aria-hidden="true"></i>
                                </button>
                            </div>
                            <div class="col-xs-12 col-md-9">
                                <input type="text" id="smtp_host" class="form-control" placeholder="smtp.example.com" style="max-width:400px;" />
                            </div>
                        </div>

                        <div class="row form-group">
                            <div class="col-xs-12 col-md-3">
                                <label>{{ devicemonitor_t('SMTP Port') }}:</label>
                            </div>
                            <div class="col-xs-12 col-md-9">
                                <input type="number" id="smtp_port" class="form-control" value="587" min="1" max="65535" style="width:120px;" />
                            </div>
                        </div>

                        <div class="row form-group">
                            <div class="col-xs-12 col-md-3">
                                <label>{{ devicemonitor_t('Encryption') }}:</label>
                            </div>
                            <div class="col-xs-12 col-md-9">
                                <select id="smtp_encryption" class="selectpicker" data-style="btn-default" data-width="180px">
                                    <option value="starttls">STARTTLS</option>
                                    <option value="ssl">SSL/TLS</option>
                                    <option value="none">{{ devicemonitor_t('None') }}</option>
                                </select>
                            </div>
                        </div>

                        <div class="row form-group">
                            <div class="col-xs-12 col-md-3">
                                <label>{{ devicemonitor_t('SMTP Username') }}:</label>
                                <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About SMTP Username') }}"
                                        data-content="{{ devicemonitor_t('Leave empty if the SMTP server does not require authentication') }}">
                                    <i class="fa fa-info-circle" aria-hidden="true"></i>
                                </button>
                            </div>
                            <div class="col-xs-12 col-md-9">
                                <input type="text" id="smtp_username" class="form-control" autocomplete="username" style="max-width:400px;" />
                            </div>
                        </div>

                        <div class="row form-group">
                            <div class="col-xs-12 col-md-3">
                                <label>{{ devicemonitor_t('SMTP Password') }}:</label>
                            </div>
                            <div class="col-xs-12 col-md-9">
                                <input type="password" id="smtp_password" class="form-control" autocomplete="new-password" style="max-width:400px;" />
                            </div>
                        </div>
                    </div>

                    <div class="row form-group">
                        <div class="col-xs-12 col-md-3">
                            <strong>{{ devicemonitor_t('Test Email') }}</strong>
                            <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Test Email') }}"
                                    data-content="{{ devicemonitor_t('The current email settings are saved before the test is sent') }}">
                                <i class="fa fa-info-circle" aria-hidden="true"></i>
                            </button>
                        </div>
                        <div class="col-xs-12 col-md-9">
                            <button type="button" id="btn-test-email" class="btn btn-default btn-sm" style="margin-top:14px;">
                                🧪 {{ devicemonitor_t('Test Email') }}
                            </button>
                        </div>
                    </div>
                </div>
                <div class="row" style="margin-bottom:25px;">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Infrastructure Services') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Infrastructure Service Alerts') }}"
                                data-content="{{ devicemonitor_t('Alert only on verified or authoritative infrastructure-service evidence.') }} {{ devicemonitor_t('Generic service-changed events remain history-only in this version.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="service_email_enabled" />
                            <strong>{{ devicemonitor_t('Email infrastructure service alerts') }}</strong>
                        </label>
                        <div id="service_email_options" style="margin-top:10px;">
                            <label style="display:block;font-weight:normal;">
                                <input type="checkbox" id="service_email_new" />
                                {{ devicemonitor_t('New verified service') }}
                            </label>
                            <label style="display:block;font-weight:normal;">
                                <input type="checkbox" id="service_email_unavailable" />
                                {{ devicemonitor_t('Established service unavailable') }}
                            </label>
                            <label style="display:block;font-weight:normal;">
                                <input type="checkbox" id="service_email_recovered" />
                                {{ devicemonitor_t('Unavailable service recovered') }}
                            </label>
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Notify for interfaces') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Notification Interfaces') }}"
                                data-content="{{ devicemonitor_t('Leave empty to receive notifications from all interfaces') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <div style="margin-top:6px;border:1px solid #444;border-radius:4px;padding:8px;max-width:400px;max-height:180px;overflow-y:auto;" id="email-vlan-list"></div>
                    </div>
                </div>
                <div style="padding:10px 0 0 0;">
                    <button type="button" class="btn btn-primary btn-apply" id="btn-apply-email">
                        <i class="fa fa-check"></i> {{ devicemonitor_t('Apply') }}
                    </button>
                </div>
                </form>
            </div>

            <!-- TAB 4: Webhook -->
            <div role="tabpanel" class="tab-pane" id="tab-webhook">
                <form class="dm-pane-form">
                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Webhook Notifications') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Webhook Notifications') }}"
                                data-content="{{ devicemonitor_t('Enables the primary high-speed HTTP POST notification engine. This serves as the master transport route used to instantly dispatch both asset summaries (New Device Discoveries) and high-severity security events to your monitoring endpoints.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="webhook_enabled" />
                            <strong>{{ devicemonitor_t('Enable Webhook') }}</strong>
                        </label>
                    </div>
                </div>

                <div id="webhook_config">
                    <div class="row form-group">
                        <div class="col-md-3">
                            <label>{{ devicemonitor_t('Webhook URL') }}:</label>
                        </div>
                        <div class="col-md-9">
                            <input type="text" id="webhook_url" class="form-control" placeholder="https://ntfy.sh/your_topic" style="max-width:500px;" />
                            <details style="margin-top:10px;padding:12px;background:#f8f9fa;border-left:4px solid #007bff;border-radius:4px;max-width:500px;">
                                <summary style="cursor:pointer;font-weight:600;color:#495057;">💡 Examples:</summary>
                                <div style="display:flex;flex-direction:column;gap:6px;margin-top:8px;padding-top:8px;">
                                    <div><span style="display:inline-block;background:#e3f2fd;color:#1976d2;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:8px;">ntfy.sh</span><code>https://ntfy.sh/opnsense_monitor</code></div>
                                    <div><span style="display:inline-block;background:#ede7f6;color:#5e35b1;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:8px;">Discord</span><code>https://discord.com/api/webhooks/...</code></div>
                                    <div><span style="display:inline-block;background:#e8f5e9;color:#388e3c;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:8px;">Custom</span><code>https://your-server.com/webhook</code></div>
                                </div>
                            </details>
                        </div>
                    </div>

                    <div class="row form-group">
                        <div class="col-md-3">
                            <strong>{{ devicemonitor_t('Send Test Webhook') }}</strong>
                        </div>
                        <div class="col-md-9">
                            <button type="button" id="test_webhook" class="btn btn-default btn-sm">
                                🧪 {{ devicemonitor_t('Send Test') }}
                            </button>
                            <span id="webhook_test_result" style="margin-left:10px;font-weight:bold;"></span>
                        </div>
                    </div>
                </div>

                <div class="row" style="margin-bottom:25px;">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Identity conflict alerts') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('Identity conflict alerts') }}"
                                data-content="{{ devicemonitor_t('Triggers a webhook payload dispatch immediately upon detection of an existing MAC address switching between multiple IP addresses (IP Spoofing / Identity Hijacking). Recommended to leave enabled.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="identity_webhook_enabled" />
                            <strong>{{ devicemonitor_t('Enable immediate webhook identity conflict alerts') }}</strong>
                        </label>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Notify for interfaces') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Notify for interfaces') }}" data-content="{{ devicemonitor_t('Select the specific network interfaces to actively monitor for device footprint shifts and identity conflicts.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <div style="margin-top:6px;border:1px solid #444;border-radius:4px;padding:8px;max-width:500px;max-height:180px;overflow-y:auto;" id="webhook-vlan-list"></div>
                    </div>
                </div>
                <div style="padding:10px 0 0 0;">
                    <button type="button" class="btn btn-primary btn-apply" id="btn-apply-webhook">
                        <i class="fa fa-check"></i> {{ devicemonitor_t('Apply') }}
                    </button>
                </div>
                </form>
            </div>

            <!-- TAB 5: Plugin Options -->
            <div role="tabpanel" class="tab-pane" id="tab-pluginoptions">
                <form class="dm-pane-form">
                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('AdGuard DNS Rewrites') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('AdGuard DNS Rewrites') }}" data-content="{{ devicemonitor_t('Uses manually configured AdGuard Home DNS rewrites as a high-confidence hostname source. Enable this only if you use AdGuard Home.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="adguard_rewrite_enabled" />
                            <strong>{{ devicemonitor_t('Enable AdGuard DNS rewrite hostname enrichment') }}</strong>
                        </label>

                        <div id="adguard_rewrite_config" style="margin-top:14px;display:none;">
                            <div class="row form-group">
                                <div class="col-md-3">
                                    <label>{{ devicemonitor_t('AdGuard URL') }}:</label>
                                    <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('AdGuard URL') }}" data-content="{{ devicemonitor_t('HTTPS base URL of your AdGuard Home server') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                                </div>
                                <div class="col-md-9">
                                    <input type="text" id="adguard_url" class="form-control" placeholder="https://192.168.1.2" style="max-width:400px;" />
                                </div>
                            </div>

                            <div class="row form-group">
                                <div class="col-md-3">
                                    <label>{{ devicemonitor_t('Username') }}:</label>
                                </div>
                                <div class="col-md-9">
                                    <input type="text" id="adguard_username" class="form-control" autocomplete="username" style="max-width:400px;" />
                                </div>
                            </div>

                            <div class="row form-group">
                                <div class="col-md-3">
                                    <label>{{ devicemonitor_t('Password') }}:</label>
                                </div>
                                <div class="col-md-9">
                                    <input type="password" id="adguard_password" class="form-control" autocomplete="new-password" style="max-width:400px;" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Pi-hole Hostnames') }}</strong>
                        <span class="badge" style="background:#f0ad4e;color:#fff;margin-left:6px;font-weight:normal;">{{ devicemonitor_t('Experimental') }}</span>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Pi-hole Hostnames') }}" data-content="{{ devicemonitor_t('Uses Pi-hole v6 DHCP leases as a hostname source. Requires Pi-hole v6, HTTPS and an app password. Disabled by default.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="pihole_enabled" />
                            <strong>{{ devicemonitor_t('Enable Pi-hole hostname enrichment') }}</strong>
                        </label>

                        <div id="pihole_config" style="margin-top:14px;display:none;">
                            <div class="row form-group">
                                <div class="col-md-3">
                                    <label>{{ devicemonitor_t('Pi-hole URL') }}:</label>
                                    <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Pi-hole URL') }}" data-content="{{ devicemonitor_t('HTTPS base URL of your Pi-hole server') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                                </div>
                                <div class="col-md-9">
                                    <input type="text" id="pihole_url" class="form-control" placeholder="https://192.168.1.3" style="max-width:400px;" />
                                </div>
                            </div>

                            <div class="row form-group">
                                <div class="col-md-3">
                                    <label>{{ devicemonitor_t('App password') }}:</label>
                                    <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('App password') }}" data-content="{{ devicemonitor_t('Pi-hole app password generated in the Pi-hole web interface') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                                </div>
                                <div class="col-md-9">
                                    <input type="password" id="pihole_password" class="form-control" autocomplete="new-password" style="max-width:400px;" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Unbound Hostnames') }}</strong>
                        <span class="badge" style="background:#f0ad4e;color:#fff;margin-left:6px;font-weight:normal;">{{ devicemonitor_t('Experimental') }}</span>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Unbound Hostnames') }}" data-content="{{ devicemonitor_t('Reads local OPNsense Unbound host overrides and host aliases only. No network queries are made. Disabled by default.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="unbound_enabled" />
                            <strong>{{ devicemonitor_t('Enable Unbound hostname enrichment') }}</strong>
                        </label>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Plugin translations (sidecar catalogue)') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Plugin translations (sidecar catalogue)') }}" data-content="{{ devicemonitor_t('Forces the interface to use the dedicated translation file of this plugin. If disabled, labels may default to English.') }}"><i class="fa fa-info-circle" aria-hidden="true"></i></button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="sidecar_translation_enabled" />
                            <strong>{{ devicemonitor_t('Enable sidecar catalogue translations') }}</strong>
                        </label>
                    </div>
                </div>

                <div style="padding:10px 0 0 0;">
                    <button type="button"
                            class="btn btn-primary btn-apply"
                            id="btn-apply-pluginoptions">
                        <i class="fa fa-check"></i> {{ devicemonitor_t('Apply') }}
                    </button>
                </div>
                </form>
            </div>

            <!-- TAB 6: HA / CARP -->
            <div role="tabpanel" class="tab-pane" id="tab-peers">
                <div class="alert alert-info" style="font-size:12px;">
                    {{ devicemonitor_t('Read-only peer access to the Device Monitor email log. The peer URL must use https:// and TLS is always verified. Credentials are stored on this node only and are never shown again after saving. Live access stays disabled until you enable it below.') }}
                </div>
                <div class="row form-group">
                    <label class="col-md-3 control-label">{{ devicemonitor_t('Enable peer access') }}</label>
                    <div class="col-md-9">
                        <input type="checkbox" id="email_log_peer_enabled" />
                        <small class="text-muted">{{ devicemonitor_t('Off by default. Combining is attempted only when this is enabled and the settings below validate.') }}</small>
                    </div>
                </div>
                <div class="row form-group">
                    <label class="col-md-3 control-label" for="email_log_peer_url">{{ devicemonitor_t('Peer URL') }}</label>
                    <div class="col-md-9">
                        <input type="text" class="form-control" id="email_log_peer_url"
                               placeholder="https://192.168.20.252" />
                        <small class="text-muted">{{ devicemonitor_t('Absolute https URL of the peer firewall. Plain HTTP, credentials in the URL and query strings are refused.') }}</small>
                    </div>
                </div>
                <div class="row form-group">
                    <label class="col-md-3 control-label" for="email_log_peer_api_key">{{ devicemonitor_t('API key') }}</label>
                    <div class="col-md-9">
                        <input type="text" class="form-control" id="email_log_peer_api_key" autocomplete="off" />
                        <small class="text-muted">{{ devicemonitor_t('Peer user API key with read access to api/devicemonitor/emaillog/*.') }}</small>
                    </div>
                </div>
                <div class="row form-group">
                    <label class="col-md-3 control-label" for="email_log_peer_api_secret">{{ devicemonitor_t('API secret') }}</label>
                    <div class="col-md-9">
                        <input type="password" class="form-control" id="email_log_peer_api_secret" autocomplete="new-password" />
                        <small class="text-muted" id="email_log_peer_secret_state"></small>
                    </div>
                </div>
                <div class="row form-group">
                    <label class="col-md-3 control-label" for="email_log_peer_ca_pem">{{ devicemonitor_t('Trusted CA (PEM)') }}</label>
                    <div class="col-md-9">
                        <textarea class="form-control" id="email_log_peer_ca_pem" rows="4" placeholder="-----BEGIN CERTIFICATE-----"></textarea>
                        <small class="text-muted">{{ devicemonitor_t('Paste the certificate authority that signed the peer certificate, or leave empty to use the firewall trust store. Verification cannot be disabled.') }}</small>
                    </div>
                </div>
                <div class="row form-group">
                    <label class="col-md-3 control-label" for="email_log_peer_timeout">{{ devicemonitor_t('Request timeout (seconds)') }}</label>
                    <div class="col-md-9">
                        <input type="number" min="2" max="30" class="form-control" id="email_log_peer_timeout" value="8" style="max-width:120px;" />
                    </div>
                </div>
                <div class="alert alert-warning" id="email_log_peer_validation" style="display:none;font-size:12px;"></div>
            </div>
            <div role="tabpanel" class="tab-pane" id="tab-ha">
                <form class="dm-pane-form">
                <div id="dm-ha-non-ha-note" class="alert alert-info" role="note" style="display:none;">
                    <strong>{{ devicemonitor_t('No CARP configuration detected') }}</strong>
                    <div>{{ devicemonitor_t('HA controls that require a CARP role are disabled. Saved values are preserved; choose an explicit role override to enable them.') }}</div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('CARP awareness') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('CARP awareness') }}"
                                data-content="{{ devicemonitor_t('A CARP standby does not carry the monitored traffic, so hostwatch there under-reports and every liveness verdict would be wrong. With this enabled a standby node skips infrastructure-service discovery and service alerts instead of inventing outages.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="ha_carp_enabled" />
                            <strong>{{ devicemonitor_t('Defer service observation to the CARP master') }}</strong>
                        </label>
                        <div class="text-muted" style="margin-top:6px;max-width:600px;">
                            {{ devicemonitor_t('Applies to the monitored interfaces only. A node with no CARP state is unaffected, so a standalone firewall keeps observing.') }}
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Role override') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Role override') }}"
                                data-content="{{ devicemonitor_t('Automatic reads the CARP state from ifconfig. Use an explicit role when the monitored interfaces carry no CARP address of their own, or to pin a node during maintenance.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <select id="ha_role_override" class="selectpicker"
                                data-style="btn-default" data-width="260px"
                                tabindex="0"
                                aria-label="{{ devicemonitor_t('Role override') }}">
                            <option value="auto">{{ devicemonitor_t('Automatic (use CARP role)') }}</option>
                            <option value="master">{{ devicemonitor_t('Force MASTER behaviour') }}</option>
                            <option value="backup">{{ devicemonitor_t('Force BACKUP behaviour') }}</option>
                        </select>
                        <div class="text-muted" style="margin-top:6px;">
                            {{ devicemonitor_t('Overrides Device Monitor behaviour only; does not change the firewall’s CARP role.') }}
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Failover notification') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Failover notification') }}"
                                data-content="{{ devicemonitor_t('Reports a MASTER/BACKUP transition once, through the configured email and webhook channels. Without this the transition is only written to the Device Monitor log.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <label style="margin:0;">
                            <input type="checkbox" id="ha_notify_failover" />
                            <strong>{{ devicemonitor_t('Notify when this node changes CARP role') }}</strong>
                        </label>
                        <div class="text-muted" style="margin-top:6px;max-width:600px;">
                            {{ devicemonitor_t('Delivery uses whichever channels are enabled on the Email and Webhook tabs; a disabled channel is skipped.') }}
                        </div>
                    </div>
                </div>

                <div class="row form-group">
                    <div class="col-md-3">
                        <strong>{{ devicemonitor_t('Live CARP status') }}</strong>
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('More information') }}: {{ devicemonitor_t('Live CARP status') }}"
                                data-content="{{ devicemonitor_t('Read-only view of this node: the role ifconfig reports for the monitored interfaces, and the CARP virtual IPs defined on this firewall. Nothing here is saved.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="col-md-9">
                        <table class="table table-condensed dm-status-table" id="ha-status-table">
                            <tbody>
                                <tr>
                                    <td style="width:40%;color:#888;">{{ devicemonitor_t('Detected role') }}</td>
                                    <td id="ha-status-role">-</td>
                                </tr>
                                <tr>
                                    <td style="color:#888;">{{ devicemonitor_t('Effective mode') }}</td>
                                    <td id="ha-status-mode">-</td>
                                </tr>
                                <tr>
                                    <td style="color:#888;">{{ devicemonitor_t('HA policy permission') }}</td>
                                    <td id="ha-status-observation">-</td>
                                </tr>
                            </tbody>
                        </table>
                        <table class="table table-condensed dm-status-table">
                            <thead>
                                <tr>
                                    <th>{{ devicemonitor_t('Virtual IP') }}</th>
                                    <th>{{ devicemonitor_t('VHID') }}</th>
                                    <th>{{ devicemonitor_t('State') }}</th>
                                </tr>
                            </thead>
                            <tbody id="ha-status-vips">
                                <tr>
                                    <td colspan="3" class="text-muted">{{ devicemonitor_t('No CARP virtual IP defined on this firewall.') }}</td>
                                </tr>
                            </tbody>
                        </table>
                        <button type="button" class="btn btn-default btn-sm" id="btn-ha-status-refresh">
                            <i class="fa fa-refresh" aria-hidden="true"></i> {{ devicemonitor_t('Refresh') }}
                        </button>
                    </div>
                </div>

                <div style="padding:10px 0 0 0;">
                    <button type="button"
                            class="btn btn-primary btn-apply"
                            id="btn-apply-ha">
                        <i class="fa fa-check"></i> {{ devicemonitor_t('Apply') }}
                    </button>
                </div>
                </form>
            </div>


            <!-- TAB 7: About -->
            <div role="tabpanel" class="tab-pane" id="tab-about">
                <form class="dm-pane-form">
                <div style="max-width:600px;padding:10px 0;">
                    <h3 style="margin-top:0;">{{ devicemonitor_t('Device Monitor') }} <span id="about-version" style="color:#888;font-size:16px;"></span></h3>
                    <p class="text-muted">{{ devicemonitor_t('OPNsense plugin for monitoring network devices, detecting IP and MAC address conflicts, discovering infrastructure services, performing targeted security scans, and sending configurable alerts using native hostwatch data.') }}</p>
                    <table class="table table-condensed" style="margin-top:20px;">
                        <tr>
                            <th colspan="2" style="padding-top:14px;">{{ devicemonitor_t('Original Project') }}</th>
                        </tr>
                        <tr>
                            <td style="width:40%;color:#888;">{{ devicemonitor_t('Creator') }}</td>
                            <td>Hacesoft</td>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ devicemonitor_t('Repository') }}</td>
                            <td><a href="https://github.com/hacesoft/opnsense-devicemonitor" target="_blank">github.com/hacesoft/opnsense-devicemonitor</a></td>
                        </tr>

                        <tr>
                            <th colspan="2" style="padding-top:18px;"><span id="about-features-version">v2.14</span> {{ devicemonitor_t('Features and Enhancements') }}</th>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ devicemonitor_t('Developer') }}</td>
                            <td>Anthony Gonzalez</td>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ devicemonitor_t('Repository') }}</td>
                            <td><a href="https://github.com/apg19590209/opnsense-devicemonitor" target="_blank">github.com/apg19590209/opnsense-devicemonitor</a></td>
                        </tr>
                        <tr>
                            <th colspan="2" style="padding-top:18px;">{{ devicemonitor_t('Licensing & Compatibility') }}</th>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ devicemonitor_t('Licence') }}</td>
                            <td>BSD 2-Clause License</td>
                        </tr>
                        <tr>
                            <td style="color:#888;">{{ devicemonitor_t('Requires OPNsense') }}</td>
                            <td>&ge; 26.1.5</td>
                        </tr>
                    </table>
                </div>
                </form>
            </div>

        </div>
    </div>
</div>

<style>
.dm-info { border:0; background:transparent; color:#337ab7; padding:0 3px; cursor:pointer; }
/* Tab geometry lives here rather than in inline style attributes so the nav and
 * the pane area stay in step; the same classes are used by every subtab. */
.dm-settings-tabs { margin:10px 0 0 0; }
.dm-settings-panes { padding:15px 0; }
.dm-status-table { margin-bottom:8px; }
.dm-status-table td:first-child { color:#888; }
.dm-ha-node-notice { margin:10px 0 0 0; padding:9px 12px; overflow-wrap:anywhere; word-break:break-word; }
.dm-ha-node-notice-head { display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap; }
.dm-ha-node-summary { flex:1 1 240px; min-width:0; overflow-wrap:anywhere; }
.dm-ha-node-toggle { flex:0 0 auto; margin-left:auto; white-space:nowrap; }
.dm-ha-node-summary-warning { margin-top:4px; font-weight:600; }
.dm-ha-node-details { margin-top:6px; }
.dm-ha-node-details[hidden] { display:none; }
.dm-ha-node-role-facts { display:flex; flex-wrap:wrap; gap:4px 18px; margin-bottom:5px; }
.dm-ha-node-role-facts[hidden] { display:none; }
.dm-ha-node-role-facts > span { min-width:0; }
.dm-ha-node-ownership { margin-bottom:6px; }
.dm-ha-node-activity-details { margin-top:4px; }
.dm-ha-node-continuing-block { margin-top:4px; }
.dm-ha-node-paused-list { margin:5px 0 4px 20px; padding:0; }
.dm-ha-node-last-scan { margin-top:5px; font-size:12px; }
</style>
<script>
// Pure state renderer shared in behaviour with Devices. The server decides the
// HA verdict and the exact paused activity identifiers; this helper only maps
// them to translated labels. It deliberately keeps an unreadable CARP state
// distinct from non-HA and from MASTER.
function buildHaNoticeModel(data, t) {
    data = data || {};
    t = t || {};

    var status = String(data.ha_status || '').toLowerCase();
    var detected = String(data.role || data.mode || '').toUpperCase();
    var effective = String(data.mode || data.role || '').toUpperCase();

    if (data.fetch_failed === true) {
        status = 'fetch_failed';
    }

    if (['master', 'backup', 'non_ha', 'unavailable', 'fetch_failed'].indexOf(status) === -1) {
        if (data.role_available === false) {
            status = 'unavailable';
        } else if (effective === 'BACKUP') {
            status = 'backup';
        } else if (effective === 'MASTER') {
            status = 'master';
        } else {
            status = 'non_ha';
        }
    }

    var overrideName = String(data.override || 'auto').toLowerCase();
    var overrideActive = data.override_active === true || overrideName !== 'auto';
    var nonHaConfirmed = typeof data.non_ha_confirmed === 'boolean'
        ? data.non_ha_confirmed
        : (status === 'non_ha' && data.role_available === true && !overrideActive);
    var nonHaConfirmation = String(data.non_ha_confirmation || '');
    var unconfirmedNonHa = status === 'non_ha' && !nonHaConfirmed && !overrideActive;
    var haRelevant = data.ha_relevant !== false && !nonHaConfirmed;

    var activityLabels = {
        visibility_priming: t.visibility_priming,
        service_discovery: t.service_discovery,
        service_alerts: t.service_alerts,
        identity_alerts: t.identity_alerts,
        new_device_alerts: t.new_device_alerts,
        targeted_nmap: t.targeted_nmap
    };
    var paused = [];

    if (status === 'backup') {
        (data.paused_activities || []).forEach(function (id) {
            paused.push(activityLabels[id] || id);
        });
    }

    var detectedRole = (data.role_available === false || status === 'fetch_failed')
        ? t.unavailable
        : (unconfirmedNonHa
            ? t.unconfirmed
            : (detected && detected !== 'NONE'
            ? (data.role_mixed ? 'MASTER / BACKUP' : detected)
            : t.non_ha));
    var effectiveMode = effective;
    if (unconfirmedNonHa) {
        effectiveMode = t.unconfirmed;
    } else if (effectiveMode === 'NONE' || effectiveMode === '') {
        effectiveMode = (status === 'unavailable' || status === 'fetch_failed')
            ? t.unavailable
            : t.non_ha;
    }

    var tone = (status === 'fetch_failed' || status === 'unavailable')
        ? 'danger'
        : ((status === 'backup' || unconfirmedNonHa) ? 'warning' : 'info');
    var warning = '';

    if (status === 'fetch_failed') {
        warning = t.fetch_failed;
    } else if (status === 'unavailable') {
        warning = [
            t.role_unavailable,
            data.carp_aware === false
                ? t.carp_aware_off
                : (data.role_unknown_observation_continues === true
                    ? t.role_unknown_observation_continues
                    : '')
        ].filter(Boolean).join(' ');
    } else if (data.role_available === false) {
        warning = [
            data.carp_aware === false ? t.carp_aware_off : '',
            t.role_check_failed
        ].filter(Boolean).join(' ');
    } else if (data.carp_aware === false && !nonHaConfirmed) {
        warning = t.carp_aware_off;
    }

    var unconfirmedWarning = '';
    if (unconfirmedNonHa) {
        if (nonHaConfirmation === 'no_monitored_interfaces') {
            unconfirmedWarning = t.non_ha_unconfirmed_no_interfaces;
        } else if (nonHaConfirmation === 'carp_present_no_monitored_interfaces') {
            unconfirmedWarning = t.non_ha_unconfirmed_carp_no_interfaces;
        } else if (nonHaConfirmation === 'unresolved_monitored_interfaces') {
            unconfirmedWarning = t.non_ha_unconfirmed_unresolved_interfaces;
        } else if (nonHaConfirmation === 'carp_vip_configured') {
            unconfirmedWarning = t.non_ha_unconfirmed_carp_vip;
        } else {
            unconfirmedWarning = t.non_ha_unconfirmed_generic;
        }
    }
    if (unconfirmedWarning) {
        warning = [warning, unconfirmedWarning].filter(Boolean).join(' ');
    }

    var roleDiffers = detectedRole !== t.unavailable &&
        detectedRole !== t.unknown &&
        effectiveMode !== t.unavailable &&
        effectiveMode !== t.unknown &&
        detectedRole !== effectiveMode;

    var monitoringKnown = data.monitoring_enabled === true || data.monitoring_enabled === false;
    var monitoringEnabled = data.monitoring_enabled === true;
    var monitoringLabel = monitoringKnown
        ? (monitoringEnabled ? t.enabled : t.disabled)
        : t.unknown;

    var summaryParts = [data.node || t.unknown];
    if (unconfirmedNonHa) {
        summaryParts.push(t.ha_status_unconfirmed);
    } else if (!nonHaConfirmed) {
        summaryParts.push(effectiveMode);
    }
    summaryParts.push(monitoringKnown
        ? (monitoringEnabled ? t.monitoring_enabled : t.monitoring_disabled)
        : t.monitoring_status_unknown);
    if (status === 'backup' && paused.length) {
        summaryParts.push(t.some_activities_paused);
    }
    var summary = summaryParts.filter(Boolean).join(' \u00b7 ');

    var summaryWarningParts = [];
    if (overrideActive) {
        summaryWarningParts.push(t.role_override_active);
    }
    if (warning) {
        summaryWarningParts.push(warning);
    }
    if (roleDiffers && !warning) {
        summaryWarningParts.push(t.role_mode_difference);
    }
    var summaryWarning = summaryWarningParts.filter(Boolean).join(' ');

    var lastScanState = String(data.last_scan_state || '').toLowerCase();
    var lastScanTimezone = String(data.last_scan_timezone || '').trim();
    var lastScan = t.no_scan;
    if (status === 'fetch_failed') {
        lastScan = t.scan_fetch_failed;
    } else if (lastScanState === 'unavailable') {
        lastScan = t.scan_unavailable;
    } else if (data.last_scan) {
        lastScan = (t.last_scan || '') + ': ' + data.last_scan
            + ' (' + (lastScanTimezone || t.timezone_unavailable) + ')';
    }

    var activityRelevant = haRelevant && (
        status === 'master' || status === 'backup' ||
        data.role_unknown_observation_continues === true
    );

    return {
        status: status,
        tone: tone,
        haRelevant: haRelevant,
        nonHaConfirmed: nonHaConfirmed,
        overrideActive: overrideActive,
        role: detectedRole,
        mode: effectiveMode,
        node: data.node || t.unknown,
        ownership: (nonHaConfirmed || unconfirmedNonHa) ? (t.node_local || t.ownership) : t.ownership,
        paused: paused,
        pausedHeading: t.paused_activities,
        pausedNote: t.paused_note,
        continuingHeading: t.continuing_activities,
        continuation: t.continuation,
        activityRelevant: activityRelevant,
        monitoringEnabled: monitoringEnabled,
        monitoringLabel: monitoringLabel,
        summary: summary,
        summaryWarning: summaryWarning,
        roleDiffers: roleDiffers,
        lastScan: lastScan
    };
}

$().ready(function() {
    /* Each tab pane is its own form container: Enter inside a pane must not run
     * an implicit GET submit, which would reload the page and discard unsaved
     * edits. */
    $('.dm-pane-form').on('submit', function(e) { e.preventDefault(); });
    /* Bootstrap-select initialises through a window-load data hook, which runs
     * after these asynchronous settings requests. Initialise it here and keep
     * the generated control in sync when the native select's value or disabled
     * state changes. Bootstrap-select uses the native select as its keyboard
     * focus proxy, so retain the explicit tabindex on that select and let the
     * plugin manage the generated button's focus attributes. */
    function refreshHaRoleOverrideSelectpicker() {
        var $select = $('#ha_role_override');
        if (!$select.length) { return; }
        if (!$select.data('selectpicker')) {
            $select.selectpicker();
        }
        $select.selectpicker('refresh');

        var $toggle = $select.closest('.bootstrap-select').children('button.dropdown-toggle');
        if (!$toggle.length) { return; }
        var label = $select.attr('aria-label') || '';
        var selected = $select.find('option:selected').text().trim();
        if (label) {
            $toggle.attr('aria-label', selected ? label + ': ' + selected : label);
        }

        /* Bootstrap-select 1.13.18 consumes Space and Enter in its closed-state
         * type-ahead branch before the native button can activate. Open the
         * dropdown explicitly for those keys; when it is already open, leave
         * Space and Enter to the plugin so they select the active option. */
        $toggle.off('keydown.dmHaSelectpicker').on('keydown.dmHaSelectpicker', function(event) {
            var isOpen = $toggle.closest('.bootstrap-select').hasClass('open');
            if (!isOpen && (event.which === 32 || event.which === 13)) {
                event.preventDefault();
                event.stopPropagation();
                $toggle.trigger('click.bs.dropdown.data-api');
            }
        });
    }
    refreshHaRoleOverrideSelectpicker();
    /* All five configuration panes are native grid rows: every setting's guidance
     * button is authored beside its heading in the col-md-3 label column, so no
     * runtime relocation of .dm-info buttons is required. */
    $('.dm-info').popover({container:'body', placement:'auto bottom', trigger:'focus'});
    $('.dm-info').on('keydown', function(event) {
        if (event.key === 'Escape') { $(this).popover('hide').trigger('blur'); }
    });
    /* Bootstrap 3 activates a tab but never updates the ARIA state, so the
     * static aria-selected attributes would go stale after the first click.
     * Keep them truthful for assistive technology. */
    $('.dm-settings-tabs a[data-toggle="tab"]').on('shown.bs.tab', function(event) {
        $('.dm-settings-tabs a[data-toggle="tab"]').attr('aria-selected', 'false');
        $(event.target).attr('aria-selected', 'true');
    });
    /* The CARP table is a live reading: refresh it when the subtree is opened
     * rather than only when the page finished loading. */
    $('a[href="#tab-ha"]').on('shown.bs.tab', loadHaNodeVisibility);
    var returnPath = new URLSearchParams(window.location.search).get('return');
    if (returnPath && /^\/ui\/devicemonitor\/index\/devicehistory\?mac=[0-9a-fA-F:%]+$/.test(returnPath)) {
        $('#return-to-device-details').attr('href', returnPath).show();
    }
    if (window.location.hash === '#tab-email' || returnPath) {
        $('a[href="#tab-email"]').tab('show');
    }
    var translations = {
        config_saved:  {{ lang.query('Configuration saved')|json_encode(15) }},
        config_error:  {{ lang.query('Error saving configuration')|json_encode(15) }},
        test_sent:     {{ lang.query('Test email sent to')|json_encode(15) }},
        test_failed:   {{ lang.query('Failed to send email')|json_encode(15) }},
        saving:        {{ lang.query('Saving...')|json_encode(15) }},
        /* The HA / CARP status words reach the script through the same encoded
         * lang.query path as every other string here: the installer merges the
         * plugin catalogues into the core domain (DM-BL-008c), so lang.query does
         * resolve them, and only a literal accepted by the JS renderer may appear
         * inside a script body. */
        status_unknown:    {{ lang.query('unknown')|json_encode(15) }},
        status_permitted:  {{ lang.query('permitted')|json_encode(15) }},
        status_paused_by_ha: {{ lang.query('paused by HA policy')|json_encode(15) }},
        no_carp_vips:      {{ lang.query('No CARP virtual IP defined on this firewall.')|json_encode(15) }},
        unknown:           {{ lang.query('unknown')|json_encode(15) }},
        unavailable:       {{ lang.query('Unavailable')|json_encode(15) }},
        non_ha:            {{ lang.query('Non-HA')|json_encode(15) }},
        unconfirmed:       {{ lang.query('Unconfirmed')|json_encode(15) }},
        ha_status_unconfirmed: {{ lang.query('HA status unconfirmed')|json_encode(15) }},
        detected_role:     {{ lang.query('Detected role')|json_encode(15) }},
        effective_mode:    {{ lang.query('Effective mode')|json_encode(15) }},
        monitoring:        {{ lang.query('Monitoring')|json_encode(15) }},
        enabled:           {{ lang.query('Enabled')|json_encode(15) }},
        disabled:          {{ lang.query('Disabled')|json_encode(15) }},
        monitoring_enabled: {{ lang.query('Monitoring enabled')|json_encode(15) }},
        monitoring_disabled: {{ lang.query('Monitoring disabled')|json_encode(15) }},
        monitoring_status_unknown: {{ lang.query('Monitoring status unknown')|json_encode(15) }},
        some_activities_paused: {{ lang.query('Some activities paused')|json_encode(15) }},
        paused_activities: {{ lang.query('Paused activities')|json_encode(15) }},
        continuing_activities: {{ lang.query('Continuing activities')|json_encode(15) }},
        show_details:      {{ lang.query('Show details')|json_encode(15) }},
        hide_details:      {{ lang.query('Hide details')|json_encode(15) }},
        role_mode_difference: {{ lang.query('Detected and effective roles differ.')|json_encode(15) }},
        role_override_active: {{ lang.query('Role override is active.')|json_encode(15) }},
        node_local:        {{ lang.query('Node-local Device Monitor data')|json_encode(15) }},
        ownership:         {{ lang.query('Displayed data belongs to this node only and is not merged from the CARP peer.')|json_encode(15) }},
        visibility_priming: {{ lang.query('Visibility priming')|json_encode(15) }},
        service_discovery:  {{ lang.query('Service discovery')|json_encode(15) }},
        service_alerts:     {{ lang.query('Service alerts')|json_encode(15) }},
        identity_alerts:    {{ lang.query('Identity conflict alerts')|json_encode(15) }},
        new_device_alerts:  {{ lang.query('New device alerts')|json_encode(15) }},
        targeted_nmap:      {{ lang.query('Automatic targeted Nmap scans')|json_encode(15) }},
        continuation:      {{ lang.query('Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.')|json_encode(15) }},
        paused_note:       {{ lang.query('A paused activity is not an empty result.')|json_encode(15) }},
        role_unavailable:  {{ lang.query('HA role status is unavailable. Confirm CARP and the effective mode before relying on this view.')|json_encode(15) }},
        fetch_failed:      {{ lang.query('HA status could not be retrieved, so the current CARP gating state is unknown.')|json_encode(15) }},
        role_unknown_observation_continues: {{ lang.query('Device Monitor reports that observation continues while the CARP role is unknown.')|json_encode(15) }},
        carp_aware_off:    {{ lang.query('CARP awareness is disabled, so no activities are paused.')|json_encode(15) }},
        role_check_failed: {{ lang.query('The detected CARP role is unavailable; the effective mode comes from the role override.')|json_encode(15) }},
        non_ha_unconfirmed_no_interfaces: {{ lang.query('HA status is unconfirmed because no monitored interface is selected.')|json_encode(15) }},
        non_ha_unconfirmed_carp_no_interfaces: {{ lang.query('HA status is unconfirmed because CARP is configured or active on this appliance, but no monitored interface is selected; monitoring-scope roles are unknown.')|json_encode(15) }},
        non_ha_unconfirmed_unresolved_interfaces: {{ lang.query('HA status is unconfirmed because the selected monitored interfaces do not resolve to local devices.')|json_encode(15) }},
        non_ha_unconfirmed_carp_vip: {{ lang.query('HA status is unconfirmed because CARP virtual IPs are configured without a detected CARP role.')|json_encode(15) }},
        non_ha_unconfirmed_generic: {{ lang.query('HA status is unconfirmed. Confirm CARP and the selected monitored interfaces.')|json_encode(15) }},
        last_scan:         {{ lang.query('Last successful local scan')|json_encode(15) }},
        timezone_unavailable: {{ lang.query('Timezone unavailable')|json_encode(15) }},
        no_scan:           {{ lang.query('No successful local scan appears in the available scan history.')|json_encode(15) }},
        scan_unavailable:  {{ lang.query('The local scan history could not be read.')|json_encode(15) }},
        scan_fetch_failed: {{ lang.query('Scan history was not retrieved because the HA status request failed.')|json_encode(15) }}
    };

    var haStatusRequest = 0;
    var lastHaStatusData = null;

    loadHaNodeVisibility();
    setInterval(loadHaNodeVisibility, 30000);

    var allVlanNames = {};
    var monitoredInterfaces = {};

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
        $('#about-version').text(v);
        $('#about-features-version').text(v);
    });

    // Build VLAN checklist in a container
    function buildVlanCheckList(containerId, selectedVlans) {
        var $c = $('#'+containerId).empty();
        var vlans = Object.keys(allVlanNames).sort();
        if (!vlans.length) {
            $c.html(('<em style="color:#888;font-size:12px;">' + {{ lang.query('No interfaces found')|json_encode(15) }} + '</em>'));
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

    function buildMonitoredInterfaceList(selected) {
        var $c = $('#monitored-interface-list').empty();
        var names = Object.keys(monitoredInterfaces).sort();
        if (!names.length) {
            $c.html(('<em style="color:#888;font-size:12px;">' + {{ lang.query('No enabled IPv4 interfaces found')|json_encode(15) }} + '</em>'));
            updateMonitoredWarning();
            return;
        }
        var sel = selected ? selected.split(',').map(function(v){return v.trim();}).filter(Boolean) : [];
        names.forEach(function(name) {
            var it = monitoredInterfaces[name] || {};
            var parts = [name];
            if (it.description && it.description !== name) parts.push(it.description);
            if (it.device) parts.push(it.device);
            if (it.ipaddr) parts.push(it.ipaddr + '/' + (it.subnet || ''));
            var label = parts.join(' \u2013 ');
            $c.append($('<label>').css({display:'block',margin:'3px 0',fontWeight:'normal',cursor:'pointer'}).append(
                $('<input type="checkbox" class="monitored-iface-cb">').val(name).prop('checked', sel.indexOf(name) !== -1),
                $('<span>').css('margin-left','8px').text(label)
            ));
        });
        updateMonitoredWarning();
    }

    function getSelectedMonitoredInterfaces() {
        var sel = [];
        $('#monitored-interface-list .monitored-iface-cb:checked').each(function(){ sel.push($(this).val()); });
        return sel.join(',');
    }

    function updateMonitoredWarning() {
        var enabled = $('#enabled').is(':checked');
        var selected = $('#monitored-interface-list .monitored-iface-cb:checked').length > 0;
        $('#monitored-interface-warning').toggle(enabled && !selected);
    }

    function loadConfig() {
        $.ajax({ url:'/api/devicemonitor/config/get', type:'GET', success:function(d) {
            $('#enabled').prop('checked', d.enabled==='1');
            $('#scan_interval').val(d.scan_interval||300);
            $('#adguard_rewrite_enabled').prop('checked', d.adguard_rewrite_enabled==='1');
            $('#adguard_url').val(d.adguard_url||'');
            $('#adguard_username').val(d.adguard_username||'');
            $('#adguard_password').val(d.adguard_password||'');
            $('#pihole_enabled').prop('checked', d.pihole_enabled==='1');
            $('#pihole_url').val(d.pihole_url||'');
            $('#pihole_password').val(d.pihole_password||'');
            $('#unbound_enabled').prop('checked', d.unbound_enabled==='1');
            /* HA / CARP: an absent key means "not yet written", so fall back to
             * the defaults in defaults.json rather than unchecking the box. */
            $('#ha_carp_enabled').prop('checked', d.ha_carp_enabled===undefined ? true : d.ha_carp_enabled==='1');
            $('#ha_notify_failover').prop('checked', d.ha_notify_failover==='1');
            $('#ha_role_override').val(d.ha_role_override||'auto');
            refreshHaRoleOverrideSelectpicker();
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
            $('#nmap_timing').selectpicker('refresh');
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
            $('#sidecar_translation_enabled').prop(
                'checked',
                String(
                    d.sidecar_translation_enabled !== undefined &&
                    d.sidecar_translation_enabled !== null
                        ? d.sidecar_translation_enabled
                        : '1'
                ) === '1'
            );
            $('#email_enabled').prop('checked', d.email_enabled==='1');
            $('#identity_webhook_enabled').prop('checked', d.identity_webhook_enabled==='1');
            $('#service_email_enabled').prop('checked', d.service_email_enabled==='1');
            $('#service_email_new').prop('checked', d.service_email_new===undefined ? true : d.service_email_new==='1');
            $('#service_email_unavailable').prop('checked', d.service_email_unavailable===undefined ? true : d.service_email_unavailable==='1');
            $('#service_email_recovered').prop('checked', d.service_email_recovered===undefined ? true : d.service_email_recovered==='1');
            $('#email_to').val(d.email_to||'');
            $.each(['email_reminder_scan','email_reminder_service','email_reminder_identity','email_reminder_new_device'], function(i, key) {
                $('#' + key).val((d[key] === undefined || d[key] === null) ? 0 : d[key]);
            });
            $('#email_from').val(d.email_from||'devicemonitor@opnsense.local');
            $('#email_method').val(d.email_method||'sendmail');
            $('#email_method').selectpicker('refresh');
            $('#smtp_host').val(d.smtp_host||'');
            $('#smtp_port').val(d.smtp_port||587);
            var smtpEncryptionDefault = (parseInt($('#smtp_port').val(), 10) === 25) ? 'none' : 'starttls';
            $('#smtp_encryption').val(d.smtp_encryption||smtpEncryptionDefault);
            $('#smtp_encryption').selectpicker('refresh');
            $('#smtp_username').val(d.smtp_username||'');
            $('#smtp_password').val(d.smtp_password||'');
            $('#webhook_enabled').prop('checked', d.webhook_enabled==='1');
            $('#webhook_url').val(d.webhook_url||'');
            $('#email_log_peer_enabled').prop('checked', d.email_log_peer_enabled==='1');
            $('#email_log_peer_url').val(d.email_log_peer_url||'');
            $('#email_log_peer_api_key').val(d.email_log_peer_api_key||'');
            $('#email_log_peer_ca_pem').val(d.email_log_peer_ca_pem||'');
            $('#email_log_peer_timeout').val(d.email_log_peer_timeout||8);
            /* The secret is never returned by the API. Show only whether one is stored,
             * and leave the field blank unless the operator types a replacement. */
            $('#email_log_peer_api_secret').val('');
            var hasSecret = d.email_log_peer_secret_set === true || d.email_log_peer_secret_set === '1';
            $('#email_log_peer_secret_state').text(hasSecret
                ? {{ devicemonitor_t('A peer API secret is stored. Leave blank to keep it; enter a new value to replace it.')|json_encode(15) }}
                : {{ devicemonitor_t('No peer API secret is stored.')|json_encode(15) }});
            buildVlanCheckList('email-vlan-list',   d.email_vlans   || '');
            buildVlanCheckList('webhook-vlan-list', d.webhook_vlans || '');
            buildMonitoredInterfaceList(d.monitored_interfaces || '');
            updateMonitoredWarning();
            toggleEmailConfig();
            toggleServiceEmailOptions();
            toggleEmailMethod();
            toggleWebhookConfig();
            toggleAdGuardConfig();
            togglePiHoleConfig();
            toggleUnboundConfig();
            updateHaControls(lastHaStatusData);
            loadHaNodeVisibility();
        }});
    }

    function toggleEmailConfig() {
        $('#email_enabled').prop('checked') ? $('#email_config').slideDown() : $('#email_config').slideUp();
    }
    function toggleServiceEmailOptions() {
        $('#service_email_enabled').prop('checked') ? $('#service_email_options').slideDown() : $('#service_email_options').slideUp();
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
    function toggleAdGuardConfig() {
        $('#adguard_rewrite_enabled').prop('checked') ? $('#adguard_rewrite_config').slideDown() : $('#adguard_rewrite_config').slideUp();
    }
    function togglePiHoleConfig() {
        $('#pihole_enabled').prop('checked') ? $('#pihole_config').slideDown() : $('#pihole_config').slideUp();
    }
    function toggleUnboundConfig() {
        // Unbound has no nested configuration; the control only exposes the
        // enable/disable checkbox. Kept as a no-op for symmetry with the other
        // providers so the checkbox state is simply read on save.
    }

    /* A detected non-HA node has no CARP role for these controls to affect.
     * Disable only controls that need CARP, retain their current values, and
     * keep the role override editable so an operator can inspect or clear it
     * (or choose one to make the HA controls relevant again). Unknown states
     * must leave every control available. */
    function updateHaControls(statusData) {
        if (statusData !== undefined) {
            lastHaStatusData = statusData;
        }

        var data = lastHaStatusData || {};
        var overrideName = String($('#ha_role_override').val() || 'auto').toLowerCase();
        var disableForNonHa = data.non_ha_confirmed === true && overrideName === 'auto';

        $('#ha_carp_enabled').prop('disabled', disableForNonHa);
        $('#ha_notify_failover').prop('disabled', disableForNonHa);
        $('#ha_role_override').prop('disabled', false);
        $('#dm-ha-non-ha-note').toggle(disableForNonHa);
        refreshHaRoleOverrideSelectpicker();
    }

    var haNoticeExpanded = false;

    function setHaNoticeExpanded(expanded) {
        haNoticeExpanded = !!expanded;
        $('#dm-ha-node-toggle').attr('aria-expanded', haNoticeExpanded ? 'true' : 'false');
        $('#dm-ha-node-toggle-label').text(
            haNoticeExpanded ? translations.hide_details : translations.show_details
        );
        $('#dm-ha-node-details').prop('hidden', !haNoticeExpanded).toggle(haNoticeExpanded);
    }

    function toggleHaNotice() {
        setHaNoticeExpanded(!haNoticeExpanded);
    }

    function renderHaNotice(data) {
        var model = buildHaNoticeModel(data, translations);
        var $notice = $('#dm-ha-node-notice');
        var showPaused = model.paused.length > 0;

        $notice
            .removeClass('alert-info alert-warning alert-danger')
            .addClass('alert-' + model.tone);
        $('#dm-ha-node-role').text(model.role || translations.unknown);
        $('#dm-ha-node-mode').text(model.mode || translations.unknown);
        $('#dm-ha-node-summary').text(model.summary || '');
        $('#dm-ha-node-summary-warning')
            .text(model.summaryWarning || '')
            .toggle(!!model.summaryWarning);
        $('#dm-ha-node-role-facts').toggle(model.haRelevant);
        $('#dm-ha-node-activity-details').toggle(model.activityRelevant);
        $('#dm-ha-node-ownership').text(model.ownership || '');
        $('#dm-ha-node-paused-block').toggle(model.activityRelevant && showPaused);
        $('#dm-ha-node-paused-heading').text(model.pausedHeading || '');
        $('#dm-ha-node-paused-note').text(model.pausedNote || '');
        $('#dm-ha-node-continuing-block')
            .toggle(model.activityRelevant && !!model.continuation);
        $('#dm-ha-node-continuing-heading').text(model.continuingHeading || '');
        $('#dm-ha-node-continuation').text(model.continuation || '');
        $('#dm-ha-node-last-scan').text(model.lastScan || '');

        var $paused = $('#dm-ha-node-paused').empty();
        model.paused.forEach(function (label) {
            $paused.append($('<li>').text(label));
        });
    }

    /* Render the existing HA / CARP table from the same response as the notice.
     * `unavailable` deliberately clears the VIP body as well as the three role
     * fields: an old MASTER row must not survive a failed refresh. */
    function renderHaStatus(data, unavailable) {
        data = data || {};
        var model = buildHaNoticeModel(data, translations);

        $('#ha-status-role').text(model.role || translations.status_unknown);
        $('#ha-status-mode').text(model.mode || translations.status_unknown);
        $('#ha-status-observation').text(
            unavailable
                ? translations.status_unknown
                : (data.observing ? translations.status_permitted
                                  : translations.status_paused_by_ha)
        );

        var $body = $('#ha-status-vips').empty();

        if (unavailable) {
            $body.append(
                $('<tr>').append(
                    $('<td>').attr('colspan', 3).addClass('text-muted').text(translations.status_unknown)
                )
            );
            return;
        }

        var vips = data.vips || [];

        if (!vips.length) {
            $body.append(
                $('<tr>').append(
                    $('<td>').attr('colspan', 3).addClass('text-muted').text(translations.no_carp_vips)
                )
            );
            return;
        }

        vips.forEach(function(v) {
            $body.append(
                $('<tr>').append(
                    $('<td>').text(v.vip || ''),
                    $('<td>').text(v.vhid || ''),
                    $('<td>').text(v.state || translations.status_unknown)
                )
            );
        });
    }

    function loadHaNodeVisibility() {
        var requestId = ++haStatusRequest;
        $.ajax({
            url: '/api/devicemonitor/config/getcarpstatus',
            type: 'GET',
            cache: false,
            timeout: 10000,
            success: function (data) {
                if (requestId !== haStatusRequest) {
                    return;
                }
                data = data || {};
                lastHaStatusData = data;
                renderHaNotice(data);
                renderHaStatus(data, false);
                updateHaControls(data);
            },
            error: function () {
                if (requestId !== haStatusRequest) {
                    return;
                }
                lastHaStatusData = null;
                var unavailable = {
                    ha_status: 'fetch_failed',
                    fetch_failed: true,
                    role_available: false,
                    mode: 'NONE',
                    node: '',
                    last_scan: '',
                    last_scan_state: 'unavailable'
                };
                renderHaNotice(unavailable);
                renderHaStatus(unavailable, true);
                updateHaControls(null);
            }
        });
    }

    $('#dm-ha-node-toggle').on('click', function (event) {
        event.preventDefault();
        toggleHaNotice();
    });
    setHaNoticeExpanded(false);

    $('#ha_carp_enabled').change(function() { updateHaControls(lastHaStatusData); });
    $('#ha_role_override').change(function() { updateHaControls(lastHaStatusData); });
    $('#btn-ha-status-refresh').click(loadHaNodeVisibility);
    $('#email_enabled').change(toggleEmailConfig);
    $('#service_email_enabled').change(toggleServiceEmailOptions);
    $('#email_method').change(toggleEmailMethod);
    $('#webhook_enabled').change(toggleWebhookConfig);
    $('#adguard_rewrite_enabled').change(toggleAdGuardConfig);
    $('#pihole_enabled').change(togglePiHoleConfig);
    $('#unbound_enabled').change(toggleUnboundConfig);
    $('#enabled').change(updateMonitoredWarning);
    $('#monitored-interface-list').on('change', '.monitored-iface-cb', updateMonitoredWarning);

    function collectConfigData() {
        var data = {
            enabled:          $('#enabled').is(':checked')?'1':'0',
            adguard_rewrite_enabled: $('#adguard_rewrite_enabled').is(':checked')?'1':'0',
            adguard_url:      $('#adguard_url').val(),
            adguard_username: $('#adguard_username').val(),
            adguard_password: $('#adguard_password').val(),
            pihole_enabled:  $('#pihole_enabled').is(':checked')?'1':'0',
            pihole_url:      $('#pihole_url').val(),
            pihole_password: $('#pihole_password').val(),
            unbound_enabled: $('#unbound_enabled').is(':checked')?'1':'0',
            ha_carp_enabled: $('#ha_carp_enabled').is(':checked')?'1':'0',
            ha_role_override: $('#ha_role_override').val(),
            ha_notify_failover: $('#ha_notify_failover').is(':checked')?'1':'0',
            email_enabled:    $('#email_enabled').is(':checked')?'1':'0',
            service_email_enabled: $('#service_email_enabled').is(':checked')?'1':'0',
            service_email_new: $('#service_email_new').is(':checked')?'1':'0',
            service_email_unavailable: $('#service_email_unavailable').is(':checked')?'1':'0',
            service_email_recovered: $('#service_email_recovered').is(':checked')?'1':'0',
            email_to:         $('#email_to').val(),
            email_reminder_scan:         $('#email_reminder_scan').val()||'0',
            email_reminder_service:      $('#email_reminder_service').val()||'0',
            email_reminder_identity:     $('#email_reminder_identity').val()||'0',
            email_reminder_new_device:   $('#email_reminder_new_device').val()||'0',
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
            identity_webhook_enabled: $('#identity_webhook_enabled').is(':checked')?'1':'0',
            webhook_vlans:    getSelectedVlans('webhook-vlan-list'),
            monitored_interfaces: getSelectedMonitoredInterfaces(),
            scan_interval: $('#scan_interval').val(),
            targeted_nmap_enabled: $('#targeted_nmap_enabled').is(':checked')?'1':'0',
            nmap_top_ports: $('#nmap_top_ports').val(),
            nmap_timing: $('#nmap_timing').val(),
            nmap_host_timeout: $('#nmap_host_timeout').val(),
            nmap_version_detection: $('#nmap_version_detection').is(':checked')?'1':'0',
            nmap_max_per_cycle: $('#nmap_max_per_cycle').val(),
            sidecar_translation_enabled: $('#sidecar_translation_enabled').is(':checked')?'1':'0',
            email_log_peer_enabled: $('#email_log_peer_enabled').is(':checked')?'1':'0',
            email_log_peer_url: $('#email_log_peer_url').val(),
            email_log_peer_api_key: $('#email_log_peer_api_key').val(),
            email_log_peer_ca_pem: $('#email_log_peer_ca_pem').val(),
            email_log_peer_timeout: $('#email_log_peer_timeout').val()
        };
        // An empty field means "keep the stored secret"; only send a replacement.
        var secret = $('#email_log_peer_api_secret').val();
        if (secret !== '' && secret !== undefined) {
            data.email_log_peer_api_secret = secret;
        }
        return data;
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

    /* Every pane shares one save path, so the CARP status is refreshed after a
     * successful save: toggling awareness changes what the daemon will do on the
     * next cycle and the read-only table must not keep the previous verdict. */
    $('.btn-apply').click(function(){
        saveConfig($(this), function() {
            showToast(translations.config_saved, 'success');
            loadHaNodeVisibility();
        });
    });

    $('#btn-test-email').click(function() {
        var email=$('#email_to').val();
        if (!email) { showToast({{ lang.query('Please enter recipient email first')|json_encode(15) }},'error'); return; }
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
        if (!url) { $('#webhook_test_result').html(('<span style="color:red;">❌ ' + {{ lang.query('Enter webhook URL first')|json_encode(15) }} + '</span>')); return; }
        $('#webhook_test_result').html(('<span style="color:blue;">⏳ ' + {{ lang.query('Sending...')|json_encode(15) }} + '</span>'));
        $.ajax({ url:'/api/devicemonitor/config/testWebhook', type:'POST', data:{webhook_url:url},
            success:function(d) {
                var ok = d.result==='ok';
                $('#webhook_test_result').show().html(ok
                    ? ('<span style="color:green;">✅ ' + {{ lang.query('Test sent!')|json_encode(15) }} + '</span>')
                    : '<span style="color:red;">❌ '+(d.message||{{ lang.query('Failed')|json_encode(15) }})+'</span>');
                if (ok) {
                    /* The success banner fades out after three seconds; the
                     * callback clears it and restores display so the next test
                     * result is visible. */
                    setTimeout(function() {
                        $('#webhook_test_result').fadeOut(400, function() {
                            $(this).html('').show();
                        });
                    }, 3000);
                }
            }
        });
    });

    // Load interfaces then config
    $.ajax({ url:'/api/devicemonitor/config/getinterfaces', type:'GET',
        success:function(data){
            allVlanNames = data || {};
            $.ajax({ url:'/api/devicemonitor/config/getmonitoredinterfaces', type:'GET',
                success:function(monData){ monitoredInterfaces = monData || {}; loadConfig(); },
                error:function(){ loadConfig(); }
            });
        },
        error:function(){
            $.ajax({ url:'/api/devicemonitor/config/getmonitoredinterfaces', type:'GET',
                success:function(monData){ monitoredInterfaces = monData || {}; loadConfig(); },
                error:function(){ loadConfig(); }
            });
        }
    });
});
</script>
