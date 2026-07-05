const state = {
    latestScan: null,
    latestFindings: [],
    latestReports: [],
    latestInventory: null,
    latestDependencies: [],
};

const pageTitle = document.getElementById("pageTitle");
const engineVersion = document.getElementById("engineVersion");
const toast = document.getElementById("toast");

const metricScore = document.getElementById("metricScore");
const metricRisk = document.getElementById("metricRisk");
const metricPolicy = document.getElementById("metricPolicy");
const metricFindings = document.getElementById("metricFindings");
const metricGate = document.getElementById("metricGate");

const orbScore = document.getElementById("orbScore");
const orbStatus = document.getElementById("orbStatus");
const orbDescription = document.getElementById("orbDescription");
const riskOrb = document.getElementById("riskOrb");

const severityBars = document.getElementById("severityBars");
const topDrivers = document.getElementById("topDrivers");
const scanSummaryTable = document.getElementById("scanSummaryTable");

const findingsList = document.getElementById("findingsList");
const findingCountBadge = document.getElementById("findingCountBadge");

const reportsList = document.getElementById("reportsList");
const policyPanel = document.getElementById("policyPanel");
const policyBadge = document.getElementById("policyBadge");
const comparisonResult = document.getElementById("comparisonResult");

const inventorySummary = document.getElementById("inventorySummary");
const inventoryList = document.getElementById("inventoryList");
const inventoryCountBadge = document.getElementById("inventoryCountBadge");

const pageNames = {
    overview: "Security Command Center",
    scanner: "Repository Scanner",
    inventory: "SBOM-lite Dependency Inventory",
    compare: "Before / After Comparison",
    findings: "Findings Explorer",
    policy: "Policy-as-Code",
    reports: "Report Center",
    cicd: "CI/CD Pipeline",
    about: "Project Capabilities",
};

document.querySelectorAll(".nav-link").forEach((button) => {
    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });
});

function showPage(page) {
    document.querySelectorAll(".nav-link").forEach((button) => {
        button.classList.toggle("active", button.dataset.page === page);
    });

    document.querySelectorAll(".page").forEach((section) => {
        section.classList.toggle("active", section.id === page);
    });

    pageTitle.textContent = pageNames[page] || "BuildShield-CI";
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 3200);
}

async function apiGet(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    return response.json();
}

async function apiPost(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || `Request failed: ${response.status}`);
    }

    return data;
}

function selectedReportFormats() {
    const formats = [];

    if (document.getElementById("formatJson").checked) formats.push("json");
    if (document.getElementById("formatMd").checked) formats.push("md");
    if (document.getElementById("formatHtml").checked) formats.push("html");
    if (document.getElementById("formatSarif").checked) formats.push("sarif");

    return formats.length ? formats : ["json"];
}

function policyStatusText(policyEvaluation) {
    if (!policyEvaluation) return "N/A";
    return policyEvaluation.passed ? "PASSED" : "FAILED";
}

function updateMetrics(data) {
    const summary = data.summary;
    const riskProfile = data.risk_profile;
    const policy = data.policy_evaluation;

    metricScore.textContent = `${summary.security_score}/100`;
    metricRisk.textContent = summary.risk_level;
    metricPolicy.textContent = policyStatusText(policy);
    metricFindings.textContent = summary.findings_count;
    metricGate.textContent = riskProfile.build_gate_status;

    orbScore.textContent = summary.security_score;
    orbStatus.textContent = `${summary.risk_level} Risk`;
    orbDescription.textContent = `${summary.findings_count} findings detected. Build gate ${riskProfile.build_gate_status}.`;

    const degrees = Math.max(0, Math.min(100, summary.security_score)) * 3.6;
    const color = summary.security_score >= 85
        ? "var(--green)"
        : summary.security_score >= 70
            ? "var(--yellow)"
            : "var(--red)";

    riskOrb.style.background = `
        radial-gradient(circle, #0f172a 44%, transparent 45%),
        conic-gradient(${color} ${degrees}deg, rgba(38, 56, 83, 0.75) ${degrees}deg)
    `;
}

function renderSeverityBars(summary) {
    const values = [
        ["Critical", summary.critical_count, "critical"],
        ["High", summary.high_count, "high"],
        ["Medium", summary.medium_count, "medium"],
        ["Low", summary.low_count, "low"],
        ["Info", summary.info_count, "info"],
    ];

    const max = Math.max(...values.map((item) => item[1]), 1);

    severityBars.innerHTML = values.map(([label, count, cls]) => {
        const width = Math.max(4, (count / max) * 100);

        return `
            <div class="severity-row">
                <strong>${label}</strong>
                <div class="bar-track">
                    <div class="bar-fill fill-${cls}" style="width:${width}%"></div>
                </div>
                <span>${count}</span>
            </div>
        `;
    }).join("");
}

function renderTopDrivers(riskProfile) {
    const drivers = riskProfile.top_risk_drivers || [];

    if (!drivers.length) {
        topDrivers.innerHTML = `<p class="muted">No top risk drivers detected.</p>`;
        return;
    }

    topDrivers.innerHTML = drivers.slice(0, 5).map((driver, index) => {
        return `
            <div class="driver-card">
                <div>
                    <strong>${index + 1}. ${driver.rule_id}</strong>
                    <p>${driver.title}</p>
                    <span>${driver.category} • ${driver.severity}</span>
                </div>
                <strong>${driver.contribution_points}</strong>
            </div>
        `;
    }).join("");
}

function renderScanSummary(data) {
    const summary = data.summary;
    const riskProfile = data.risk_profile;

    scanSummaryTable.innerHTML = `
        <table class="data-table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Target Path</td><td>${summary.target_path}</td></tr>
            <tr><td>Files Discovered</td><td>${summary.files_discovered}</td></tr>
            <tr><td>Files Scanned</td><td>${summary.files_scanned}</td></tr>
            <tr><td>Findings</td><td>${summary.findings_count}</td></tr>
            <tr><td>Security Score</td><td>${summary.security_score}/100</td></tr>
            <tr><td>Risk Level</td><td>${summary.risk_level}</td></tr>
            <tr><td>Build Gate</td><td>${riskProfile.build_gate_status}</td></tr>
            <tr><td>Build Gate Reason</td><td>${riskProfile.build_gate_reason}</td></tr>
        </table>
    `;
}

function severityClass(severity) {
    return String(severity || "").toLowerCase();
}

function renderFindings(findings) {
    findingCountBadge.textContent = `${findings.length} findings`;

    if (!findings.length) {
        findingsList.innerHTML = `<p class="muted">No security findings detected.</p>`;
        return;
    }

    findingsList.innerHTML = findings.map((finding) => {
        const evidence = finding.evidence || {};

        return `
            <div class="finding-card ${severityClass(finding.severity)}">
                <h4>${finding.rule_id}: ${finding.title}</h4>
                <div class="finding-meta">
                    <span>${finding.severity}</span>
                    <span>${finding.category}</span>
                    <span>${finding.confidence}</span>
                    <span>${evidence.file_path || "unknown"}:${evidence.line_number || "-"}</span>
                </div>
                <p><strong>Description:</strong> ${finding.description}</p>
                <p><strong>Impact:</strong> ${finding.impact}</p>
                <p><strong>Evidence:</strong> <code>${evidence.snippet || "N/A"}</code></p>
                <p><strong>Remediation:</strong> ${finding.remediation}</p>
            </div>
        `;
    }).join("");
}

function applyFindingFilters() {
    const query = document.getElementById("findingSearch").value.toLowerCase();
    const severity = document.getElementById("severityFilter").value;

    const filtered = state.latestFindings.filter((finding) => {
        const evidence = finding.evidence || {};
        const searchable = [
            finding.rule_id,
            finding.title,
            finding.severity,
            finding.category,
            finding.description,
            evidence.file_path,
            evidence.snippet,
        ].join(" ").toLowerCase();

        const matchesQuery = searchable.includes(query);
        const matchesSeverity = severity === "ALL" || finding.severity === severity;

        return matchesQuery && matchesSeverity;
    });

    renderFindings(filtered);
}

function renderPolicy(policy) {
    if (!policy) {
        policyBadge.textContent = "Not evaluated";
        policyPanel.innerHTML = `<p class="muted">Run a scan with policy file to view policy violations.</p>`;
        return;
    }

    policyBadge.textContent = policy.passed ? "PASSED" : "FAILED";
    policyBadge.className = policy.passed ? "chip success" : "chip";

    if (policy.passed) {
        policyPanel.innerHTML = `
            <div class="policy-card passed">
                <h4>Policy Passed</h4>
                <p>Minimum Score: ${policy.minimum_score}/100</p>
                <p>Actual Score: ${policy.actual_score}/100</p>
                <p>No policy violations detected.</p>
            </div>
        `;
        return;
    }

    policyPanel.innerHTML = `
        <div class="policy-card failed">
            <h4>Policy Failed</h4>
            <p>Minimum Score: ${policy.minimum_score}/100</p>
            <p>Actual Score: ${policy.actual_score}/100</p>
            <p>Total Violations: ${policy.violations.length}</p>
        </div>
        ${policy.violations.map((violation) => `
            <div class="policy-card failed">
                <h4>${violation.policy_id}</h4>
                <p><strong>Severity:</strong> ${violation.severity}</p>
                <p>${violation.message}</p>
            </div>
        `).join("")}
    `;
}

function renderReports(reports) {
    state.latestReports = reports;

    if (!reports.length) {
        reportsList.innerHTML = `<p class="muted">No reports generated yet.</p>`;
        return;
    }

    reportsList.innerHTML = reports.map((report) => {
        const extension = report.filename.split(".").pop().toUpperCase();

        return `
            <div class="report-card">
                <span class="chip">${extension}</span>
                <h4>${report.filename}</h4>
                <p>Run ID: ${report.run_id || "current"}</p>
                <a href="${report.download_url}" target="_blank">Download report</a>
            </div>
        `;
    }).join("");
}

function renderComparison(data) {
    const comparison = data.comparison;

    comparisonResult.innerHTML = `
        <div class="comparison-grid">
            <div class="comparison-item">
                <span>Verdict</span>
                <strong>${comparison.verdict}</strong>
            </div>
            <div class="comparison-item">
                <span>Score Improvement</span>
                <strong>${comparison.score_delta > 0 ? "+" : ""}${comparison.score_delta}</strong>
            </div>
            <div class="comparison-item">
                <span>Findings Reduced</span>
                <strong>${comparison.findings_reduced}</strong>
            </div>
            <div class="comparison-item">
                <span>Risk Reduction</span>
                <strong>${comparison.risk_reduction_percentage}%</strong>
            </div>
        </div>
    `;
}

function renderInventorySummary(summary) {
    inventorySummary.innerHTML = `
        <div class="mini-card"><span>Total Dependencies</span><strong>${summary.total_dependencies}</strong></div>
        <div class="mini-card"><span>Pinned</span><strong>${summary.pinned_dependencies}</strong></div>
        <div class="mini-card"><span>Loose</span><strong>${summary.loose_dependencies}</strong></div>
        <div class="mini-card"><span>Internal Candidates</span><strong>${summary.internal_candidate_dependencies}</strong></div>
        <div class="mini-card"><span>Missing Private Registry</span><strong>${summary.dependencies_missing_private_registry}</strong></div>
    `;
}

function renderInventoryDependencies(dependencies) {
    inventoryCountBadge.textContent = `${dependencies.length} packages`;

    if (!dependencies.length) {
        inventoryList.innerHTML = `<p class="muted">No dependencies discovered.</p>`;
        return;
    }

    inventoryList.innerHTML = `
        <table class="inventory-table">
            <thead>
                <tr>
                    <th>Ecosystem</th>
                    <th>Package</th>
                    <th>Version</th>
                    <th>Group</th>
                    <th>Pinned</th>
                    <th>Internal</th>
                    <th>File</th>
                    <th>Risk Indicators</th>
                </tr>
            </thead>
            <tbody>
                ${dependencies.map((dependency) => {
                    const indicators = dependency.risk_indicators || [];
                    const indicatorHtml = indicators.map((indicator) => {
                        const isDanger = indicator !== "LOW_RISK_DECLARATION";
                        return `<span class="risk-tag ${isDanger ? "danger" : ""}">${indicator}</span>`;
                    }).join("");

                    return `
                        <tr>
                            <td>${dependency.ecosystem}</td>
                            <td><strong>${dependency.name}</strong></td>
                            <td>${dependency.declared_version || "-"}</td>
                            <td>${dependency.dependency_group}</td>
                            <td>${dependency.is_pinned ? "YES" : "NO"}</td>
                            <td>${dependency.is_internal_candidate ? "YES" : "NO"}</td>
                            <td>${dependency.file_path}:${dependency.line_number || "-"}</td>
                            <td>${indicatorHtml}</td>
                        </tr>
                    `;
                }).join("")}
            </tbody>
        </table>
    `;
}

function applyInventoryFilters() {
    const query = document.getElementById("inventorySearch").value.toLowerCase();
    const riskFilter = document.getElementById("inventoryRiskFilter").value;

    const filtered = state.latestDependencies.filter((dependency) => {
        const indicators = dependency.risk_indicators || [];

        const searchable = [
            dependency.ecosystem,
            dependency.name,
            dependency.declared_version,
            dependency.dependency_group,
            dependency.file_path,
            indicators.join(" "),
        ].join(" ").toLowerCase();

        const matchesQuery = searchable.includes(query);
        const matchesRisk = riskFilter === "ALL" || indicators.includes(riskFilter);

        return matchesQuery && matchesRisk;
    });

    renderInventoryDependencies(filtered);
}

async function runScan(targetPath, policyPath = "buildshield-policy.yml") {
    showToast("Running scan...");

    const data = await apiPost("/api/scan", {
        target_path: targetPath,
        policy_path: policyPath,
        report_formats: selectedReportFormats(),
    });

    state.latestScan = data;
    state.latestFindings = data.findings || [];

    updateMetrics(data);
    renderSeverityBars(data.summary);
    renderTopDrivers(data.risk_profile);
    renderScanSummary(data);
    renderFindings(state.latestFindings);
    renderPolicy(data.policy_evaluation);
    renderReports(data.reports);

    showToast("Scan completed.");
    return data;
}

async function runCustomScan() {
    const targetPath = document.getElementById("targetPath").value;
    const policyPath = document.getElementById("policyPath").value;

    try {
        await runScan(targetPath, policyPath);
        showPage("overview");
    } catch (error) {
        showToast(error.message);
    }
}

async function scanVulnerable() {
    document.getElementById("targetPath").value = "samples/vulnerable-repo";

    try {
        await runScan("samples/vulnerable-repo");
        showPage("overview");
    } catch (error) {
        showToast(error.message);
    }
}

async function scanSecure() {
    document.getElementById("targetPath").value = "samples/secure-repo";

    try {
        await runScan("samples/secure-repo");
        showPage("overview");
    } catch (error) {
        showToast(error.message);
    }
}

async function runInventory(targetPath) {
    showToast("Generating dependency inventory...");

    const data = await apiPost("/api/inventory", {
        target_path: targetPath,
    });

    const inventory = data.inventory;
    state.latestInventory = inventory;
    state.latestDependencies = inventory.dependencies || [];

    renderInventorySummary(inventory.summary);
    renderInventoryDependencies(state.latestDependencies);
    renderReports(data.reports);

    showToast("SBOM-lite inventory generated.");
    showPage("inventory");

    return data;
}

async function runInventoryCustom() {
    const targetPath = document.getElementById("inventoryTarget").value;

    try {
        await runInventory(targetPath);
    } catch (error) {
        showToast(error.message);
    }
}

async function runInventoryVulnerable() {
    document.getElementById("inventoryTarget").value = "samples/vulnerable-repo";

    try {
        await runInventory("samples/vulnerable-repo");
    } catch (error) {
        showToast(error.message);
    }
}

async function runInventorySecure() {
    document.getElementById("inventoryTarget").value = "samples/secure-repo";

    try {
        await runInventory("samples/secure-repo");
    } catch (error) {
        showToast(error.message);
    }
}

async function compareSamples() {
    showToast("Running comparison...");

    try {
        const data = await apiPost("/api/compare", {
            baseline_path: "samples/vulnerable-repo",
            target_path: "samples/secure-repo",
            baseline_label: "Vulnerable Repo",
            target_label: "Secure Repo",
            report_formats: ["json", "md", "html"],
        });

        renderComparison(data);
        renderReports(data.reports);
        showPage("compare");
        showToast("Comparison completed.");
    } catch (error) {
        showToast(error.message);
    }
}

async function loadReports() {
    try {
        const data = await apiGet("/api/reports");
        renderReports(data.reports);
        showToast("Reports refreshed.");
    } catch (error) {
        showToast(error.message);
    }
}

async function initializeDashboard() {
    try {
        const health = await apiGet("/health");
        engineVersion.textContent = `${health.product} v${health.version}`;
        await loadReports();
    } catch (error) {
        engineVersion.textContent = "Backend unavailable";
    }
}

initializeDashboard();