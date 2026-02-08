#!/usr/bin/env python3
"""
Generate HTML visualizer for comparing processor inputs and outputs.
Embeds all data from different dates into a single HTML file.

Usage:
    cd /home/jonata/ceos/main-server
    python test/esfinge/generate_html_visualizer.py
"""

import json
import os
from datetime import datetime


def load_json_files(directory):
    """Load all JSON files from a directory, organized by date folders."""
    data_by_date = {}
    
    if not os.path.exists(directory):
        return data_by_date
    
    for date_folder in sorted(os.listdir(directory)):
        date_path = os.path.join(directory, date_folder)
        if not os.path.isdir(date_path):
            continue
        
        data_by_date[date_folder] = []
        
        for filename in sorted(os.listdir(date_path)):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(date_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_filename'] = filename
                    data['_date'] = date_folder
                    data_by_date[date_folder].append(data)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    
    return data_by_date


def generate_html(inputs_by_date, outputs_by_date, output_file):
    """Generate the HTML visualizer file."""
    
    all_inputs = []
    all_outputs = []
    
    for date in sorted(inputs_by_date.keys()):
        all_inputs.extend(inputs_by_date.get(date, []))
        all_outputs.extend(outputs_by_date.get(date, []))
    
    total_records = len(all_inputs)
    
    date_counts = {}
    for date in sorted(set(list(inputs_by_date.keys()) + list(outputs_by_date.keys()))):
        date_counts[date] = {
            'inputs': len(inputs_by_date.get(date, [])),
            'outputs': len(outputs_by_date.get(date, []))
        }
    
    date_buttons = ''.join(
        f'<button class="date-btn" onclick="filterByDate(\'{date}\')">{date} ({counts["inputs"]})</button>'
        for date, counts in date_counts.items()
    )
    
    # Use ensure_ascii=True to avoid any unicode issues in JS
    inputs_json = json.dumps(all_inputs, ensure_ascii=True, separators=(',', ':'))
    outputs_json = json.dumps(all_outputs, ensure_ascii=True, separators=(',', ':'))
    
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    num_dates = len(date_counts)
    
    # Write HTML with proper structure
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Esfinge Processor - Input/Output Comparison</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
        .header { background: #16213e; padding: 1rem 2rem; border-bottom: 2px solid #0f3460; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { color: #e94560; font-size: 1.5rem; }
        .filters { padding: 0.5rem 1rem; background: #0f3460; border-bottom: 1px solid #0f3460; display: flex; gap: 1rem; align-items: center; }
        .filter-group { display: flex; gap: 0.5rem; align-items: center; }
        .filter-label { color: #888; font-size: 0.8rem; }
        .date-btn { padding: 0.3rem 0.6rem; background: #1a1a2e; border: 1px solid #0f3460; border-radius: 4px; cursor: pointer; font-size: 0.75rem; color: #eee; }
        .date-btn:hover, .date-btn.active { background: #e94560; border-color: #e94560; }
        .record-selector { padding: 0.5rem 1rem; background: #16213e; border-bottom: 1px solid #0f3460; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; max-height: 80px; overflow-y: auto; }
        .record-btn { padding: 0.25rem 0.5rem; background: #1a1a2e; border: 1px solid #0f3460; border-radius: 4px; cursor: pointer; font-size: 0.7rem; color: #eee; }
        .record-btn:hover, .record-btn.active { background: #e94560; border-color: #e94560; }
        .record-btn.hidden { display: none; }
        .main { display: flex; height: calc(100vh - 280px); }
        .panel { flex: 1; border-right: 1px solid #0f3460; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
        .panel:last-child { border-right: none; }
        .panel-header { background: #16213e; padding: 0.5rem 1rem; font-weight: bold; border-bottom: 1px solid #0f3460; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .panel-header .title { color: #00d9ff; font-size: 0.9rem; }
        .panel-header .stats { font-size: 0.75rem; color: #888; }
        .panel-header .panel-actions { display: flex; gap: 0.3rem; }
        .panel-action-btn { padding: 0.2rem 0.4rem; background: #1a1a2e; border: 1px solid #0f3460; border-radius: 3px; cursor: pointer; font-size: 0.65rem; color: #888; }
        .panel-action-btn:hover { background: #0f3460; color: #eee; }
        .panel-content { flex: 1; overflow: auto; padding: 0.75rem; font-size: 0.8rem; }
        .field-row { display: flex; padding: 0.2rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .field-key { color: #e94560; min-width: 200px; padding-right: 0.5rem; font-size: 0.75rem; }
        .field-value { color: #7bed9f; word-break: break-all; font-size: 0.75rem; }
        .field-value.number { color: #70a1ff; }
        .entity-section { margin: 0.25rem 0; }
        .entity-header { background: #0f3460; padding: 0.4rem 0.6rem; border-radius: 4px; cursor: pointer; display: flex; justify-content: space-between; font-size: 0.8rem; }
        .entity-header:hover { background: #1a4a7a; }
        .entity-name { color: #00d9ff; font-weight: bold; }
        .entity-count { color: #888; font-size: 0.75rem; }
        .entity-content { margin-left: 0.75rem; padding-left: 0.75rem; border-left: 2px solid #0f3460; }
        .collapsed > .entity-content { display: none; }
        .nested-item { background: rgba(0,0,0,0.2); border-radius: 4px; padding: 0.4rem; margin-bottom: 0.3rem; }
        .nested-idx { color: #888; font-size: 0.7rem; margin-bottom: 0.2rem; }
        .json-null { color: #888; }
        .json-boolean { color: #ffa502; }
        .summary-bar { background: #0f3460; padding: 0.5rem 1rem; display: flex; gap: 2rem; font-size: 0.8rem; }
        .summary-item { display: flex; gap: 0.5rem; }
        .summary-label { color: #888; }
        .summary-value { color: #00d9ff; font-weight: bold; }
        .record-info { background: #16213e; padding: 0.3rem 1rem; font-size: 0.75rem; color: #888; border-bottom: 1px solid #0f3460; }
        .record-info strong { color: #00d9ff; }
        .entity-summary { background: #16213e; padding: 0.5rem 1rem; border-bottom: 1px solid #0f3460; display: flex; gap: 2rem; }
        .entity-summary-panel { flex: 1; }
        .entity-summary-title { color: #00d9ff; font-size: 0.8rem; font-weight: bold; margin-bottom: 0.3rem; }
        .entity-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; }
        .entity-tag { padding: 0.2rem 0.5rem; background: #0f3460; border-radius: 4px; font-size: 0.7rem; color: #7bed9f; cursor: pointer; border: 1px solid transparent; }
        .entity-tag:hover { background: #1a4a7a; border-color: #00d9ff; }
        .entity-tag .count { color: #888; margin-left: 0.3rem; }
        .entity-tag.missing { color: #e94560; background: rgba(233, 69, 96, 0.1); }
        .highlight { animation: highlight-fade 2s ease-out; }
        @keyframes highlight-fade { 0% { background-color: rgba(0, 217, 255, 0.3); } 100% { background-color: transparent; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>Esfinge Processor - Input/Output Comparison</h1>
        <div style="color:#888;font-size:0.85rem">''' + str(total_records) + ''' records loaded</div>
    </div>
    <div class="summary-bar">
        <div class="summary-item"><span class="summary-label">Total Records:</span><span class="summary-value">''' + str(total_records) + '''</span></div>
        <div class="summary-item"><span class="summary-label">Dates:</span><span class="summary-value">''' + str(num_dates) + '''</span></div>
        <div class="summary-item"><span class="summary-label">Generated:</span><span class="summary-value">''' + generated_time + '''</span></div>
    </div>
    <div class="filters">
        <div class="filter-group">
            <span class="filter-label">Filter by date:</span>
            <button class="date-btn active" onclick="filterByDate('all')">All</button>
            ''' + date_buttons + '''
        </div>
    </div>
    <div class="record-selector" id="recordSelector"></div>
    <div class="record-info" id="recordInfo">Select a record to view details</div>
    <div class="entity-summary" id="entitySummary">
        <div class="entity-summary-panel">
            <div class="entity-summary-title">Input Entities</div>
            <div class="entity-tags" id="inputEntityTags"></div>
        </div>
        <div class="entity-summary-panel">
            <div class="entity-summary-title">Output Entities</div>
            <div class="entity-tags" id="outputEntityTags"></div>
        </div>
    </div>
    <div class="main">
        <div class="panel">
            <div class="panel-header">
                <span class="title">Input (Collector Output)</span>
                <div class="panel-actions">
                    <button class="panel-action-btn" onclick="expandAll('inputPanel')">Expand All</button>
                    <button class="panel-action-btn" onclick="collapseAll('inputPanel')">Collapse All</button>
                </div>
                <span class="stats" id="inputStats">-</span>
            </div>
            <div class="panel-content" id="inputPanel"></div>
        </div>
        <div class="panel">
            <div class="panel-header">
                <span class="title">Output (Processor Result)</span>
                <div class="panel-actions">
                    <button class="panel-action-btn" onclick="expandAll('outputPanel')">Expand All</button>
                    <button class="panel-action-btn" onclick="collapseAll('outputPanel')">Collapse All</button>
                </div>
                <span class="stats" id="outputStats">-</span>
            </div>
            <div class="panel-content" id="outputPanel"></div>
        </div>
    </div>
<script>
var INPUTS = ''' + inputs_json + ''';
var OUTPUTS = ''' + outputs_json + ''';
var currentRecord = 0;
var currentDateFilter = "all";

function init() {
    renderRecordSelector();
    if (INPUTS.length > 0) selectRecord(0);
}

function expandAll(panelId) {
    var panel = document.getElementById(panelId);
    var sections = panel.querySelectorAll(".entity-section");
    for (var i = 0; i < sections.length; i++) {
        sections[i].classList.remove("collapsed");
    }
}

function collapseAll(panelId) {
    var panel = document.getElementById(panelId);
    var sections = panel.querySelectorAll(".entity-section");
    for (var i = 0; i < sections.length; i++) {
        sections[i].classList.add("collapsed");
    }
}

function filterByDate(date) {
    currentDateFilter = date;
    var btns = document.querySelectorAll(".date-btn");
    for (var i = 0; i < btns.length; i++) {
        btns[i].classList.remove("active");
        if (btns[i].textContent.indexOf(date) === 0 || (date === "all" && btns[i].textContent === "All")) {
            btns[i].classList.add("active");
        }
    }
    renderRecordSelector();
    var visible = document.querySelectorAll(".record-btn:not(.hidden)");
    if (visible.length > 0) selectRecord(parseInt(visible[0].dataset.index));
}

function renderRecordSelector() {
    var sel = document.getElementById("recordSelector");
    var html = "<span style=\\"color:#888;margin-right:0.5rem\\">Record:</span>";
    for (var i = 0; i < INPUTS.length; i++) {
        var rec = INPUTS[i];
        var dt = rec._date || "unknown";
        var fn = rec._filename || ("record_" + i);
        var proc = rec.processo_licitatorio || {};
        var pid = proc.id_procedimento_lictatorio || fn.replace(".json", "");
        var hid = currentDateFilter !== "all" && dt !== currentDateFilter;
        html += "<button class=\\"record-btn " + (i === currentRecord ? "active" : "") + (hid ? " hidden" : "") + "\\" data-index=\\"" + i + "\\" onclick=\\"selectRecord(" + i + ")\\">" + pid + "</button>";
    }
    sel.innerHTML = html;
}

function getEntityKeys(data, prefix) {
    var entities = {};
    if (!data || typeof data !== "object") return entities;
    var keys = Object.keys(data);
    for (var i = 0; i < keys.length; i++) {
        var k = keys[i];
        if (k.charAt(0) === "_") continue;
        var v = data[k];
        if (typeof v === "object" && v !== null) {
            if (Array.isArray(v)) {
                entities[k] = { count: v.length, isArray: true };
                // Check nested entities in first item
                if (v.length > 0 && typeof v[0] === "object") {
                    var nested = getEntityKeys(v[0], k);
                    var nkeys = Object.keys(nested);
                    for (var j = 0; j < nkeys.length; j++) {
                        entities[k + "." + nkeys[j]] = nested[nkeys[j]];
                    }
                }
            } else {
                entities[k] = { count: Object.keys(v).length, isArray: false };
                var nested = getEntityKeys(v, k);
                var nkeys = Object.keys(nested);
                for (var j = 0; j < nkeys.length; j++) {
                    entities[k + "." + nkeys[j]] = nested[nkeys[j]];
                }
            }
        }
    }
    return entities;
}

function renderEntitySummary(inputData, outputData) {
    var inputEntities = getEntityKeys(inputData, "");
    var outputEntities = getEntityKeys(outputData, "");
    
    var inputTags = document.getElementById("inputEntityTags");
    var outputTags = document.getElementById("outputEntityTags");
    
    var inputHtml = "";
    var ikeys = Object.keys(inputEntities).sort();
    for (var i = 0; i < ikeys.length; i++) {
        var k = ikeys[i];
        var e = inputEntities[k];
        var inOutput = outputEntities.hasOwnProperty(k);
        inputHtml += "<span class=\\"entity-tag\\" onclick=\\"scrollToEntity('inputPanel', '" + k + "')\\">" + k + "<span class=\\"count\\">" + (e.isArray ? e.count : "") + "</span></span>";
    }
    inputTags.innerHTML = inputHtml || "<span style=\\"color:#888\\">No entities</span>";
    
    var outputHtml = "";
    var okeys = Object.keys(outputEntities).sort();
    for (var i = 0; i < okeys.length; i++) {
        var k = okeys[i];
        var e = outputEntities[k];
        var inInput = inputEntities.hasOwnProperty(k);
        outputHtml += "<span class=\\"entity-tag\\" onclick=\\"scrollToEntity('outputPanel', '" + k + "')\\">" + k + "<span class=\\"count\\">" + (e.isArray ? e.count : "") + "</span></span>";
    }
    outputTags.innerHTML = outputHtml || "<span style=\\"color:#888\\">No entities</span>";
}

function scrollToEntity(panelId, entityPath) {
    var panel = document.getElementById(panelId);
    var parts = entityPath.split(".");
    var targetId = "entity-" + panelId + "-" + parts[parts.length - 1];
    var target = document.getElementById(targetId);
    
    if (!target) {
        // Try to find by text content
        var headers = panel.querySelectorAll(".entity-header .entity-name");
        for (var i = 0; i < headers.length; i++) {
            if (headers[i].textContent.trim() === parts[parts.length - 1]) {
                target = headers[i].closest(".entity-section");
                break;
            }
        }
    }
    
    if (target) {
        // Expand all parent collapsed sections
        var parent = target.parentElement;
        while (parent && parent !== panel) {
            if (parent.classList.contains("collapsed")) {
                parent.classList.remove("collapsed");
            }
            parent = parent.parentElement;
        }
        
        // Scroll into view
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        
        // Highlight
        target.classList.add("highlight");
        setTimeout(function() { target.classList.remove("highlight"); }, 2000);
    }
}

function selectRecord(idx) {
    currentRecord = idx;
    renderRecordSelector();
    var inp = INPUTS[idx];
    var out = OUTPUTS[idx];
    var info = document.getElementById("recordInfo");
    info.innerHTML = "<strong>Date:</strong> " + (inp ? inp._date : "?") + " | <strong>File:</strong> " + (inp ? inp._filename : "?");
    renderPanel("inputPanel", "inputStats", inp);
    renderPanel("outputPanel", "outputStats", out);
    renderEntitySummary(inp, out);
}

function renderPanel(pid, sid, data) {
    var p = document.getElementById(pid);
    var s = document.getElementById(sid);
    if (!data) { p.innerHTML = "<p style=\\"color:#888\\">No data</p>"; s.textContent = "-"; return; }
    s.textContent = countFields(data) + " fields";
    p.innerHTML = renderEntity(data, 0, pid);
}

function countFields(o) {
    if (typeof o !== "object" || o === null) return 1;
    if (Array.isArray(o)) { var c = 0; for (var i = 0; i < o.length; i++) c += countFields(o[i]); return c; }
    var c = 0; var keys = Object.keys(o); for (var i = 0; i < keys.length; i++) c += countFields(o[keys[i]]); return c;
}

function renderEntity(data, depth, panelId) {
    depth = depth || 0;
    panelId = panelId || "";
    if (data === null) return "<span class=\\"json-null\\">null</span>";
    if (typeof data !== "object") {
        if (typeof data === "string") return esc(data);
        if (typeof data === "number") return "<span class=\\"field-value number\\">" + data + "</span>";
        if (typeof data === "boolean") return "<span class=\\"json-boolean\\">" + data + "</span>";
        return esc(String(data));
    }
    if (Array.isArray(data)) {
        if (data.length === 0) return "[]";
        var h = "<div class=\\"nested-list\\">";
        for (var i = 0; i < data.length; i++) h += "<div class=\\"nested-item\\"><div class=\\"nested-idx\\">[" + i + "]</div>" + renderEntity(data[i], depth + 1, panelId) + "</div>";
        return h + "</div>";
    }
    var keys = Object.keys(data).sort();
    if (keys.length === 0) return "{}";
    var simple = [], complex = [];
    for (var i = 0; i < keys.length; i++) {
        var k = keys[i], v = data[k];
        if (k.charAt(0) === "_") continue;
        if (typeof v === "object" && v !== null && (Array.isArray(v) ? v.length > 0 : Object.keys(v).length > 0)) complex.push([k, v]);
        else simple.push([k, v]);
    }
    var h = "";
    for (var i = 0; i < simple.length; i++) h += "<div class=\\"field-row\\"><span class=\\"field-key\\">" + esc(simple[i][0]) + "</span><span class=\\"field-value\\">" + renderVal(simple[i][1]) + "</span></div>";
    for (var i = 0; i < complex.length; i++) {
        var ck = complex[i][0], cv = complex[i][1];
        var isA = Array.isArray(cv), cnt = isA ? cv.length : Object.keys(cv).length;
        var entityId = "entity-" + panelId + "-" + ck;
        h += "<div class=\\"entity-section\\" id=\\"" + entityId + "\\"><div class=\\"entity-header\\" onclick=\\"this.parentElement.classList.toggle('collapsed')\\"><span class=\\"entity-name\\">" + esc(ck) + "</span><span class=\\"entity-count\\">" + cnt + (isA ? " items" : " fields") + "</span></div><div class=\\"entity-content\\">" + renderEntity(cv, depth + 1, panelId) + "</div></div>";
    }
    return h;
}

function renderVal(v) {
    if (v === null) return "<span class=\\"json-null\\">null</span>";
    if (typeof v === "string") return esc(v);
    if (typeof v === "number") return v;
    if (typeof v === "boolean") return "<span class=\\"json-boolean\\">" + v + "</span>";
    if (Array.isArray(v) && v.length === 0) return "[]";
    if (typeof v === "object" && Object.keys(v).length === 0) return "{}";
    return esc(JSON.stringify(v));
}

function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

init();
</script>
</body>
</html>''')
    
    print(f"Generated: {output_file}")
    print(f"  - {total_records} records")
    print(f"  - {len(date_counts)} dates: {', '.join(date_counts.keys())}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, 'individual_inputs')
    output_dir = os.path.join(base_dir, 'individual_outputs')
    html_dir = os.path.join(base_dir, 'html_visualizer')
    
    os.makedirs(html_dir, exist_ok=True)
    
    print("Loading input files...")
    inputs_by_date = load_json_files(input_dir)
    
    print("Loading output files...")
    outputs_by_date = load_json_files(output_dir)
    
    output_file = os.path.join(html_dir, 'input_output_comparison.html')
    
    print("Generating HTML visualizer...")
    generate_html(inputs_by_date, outputs_by_date, output_file)
    
    print("\nDone! Open the HTML file in a browser to view the comparison.")


if __name__ == '__main__':
    main()
