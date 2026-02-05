// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const queryInput = document.getElementById('query-input');
const executeCheckbox = document.getElementById('execute-checkbox');
const submitBtn = document.getElementById('submit-btn');
const resultSection = document.getElementById('result-section');
const sqlQuery = document.getElementById('sql-query');
const executionResults = document.getElementById('execution-results');
const tableContainer = document.getElementById('table-container');
const errorBlock = document.getElementById('error-block');
const errorMessage = document.getElementById('error-message');
const responseTime = document.getElementById('response-time');
const apiStatus = document.getElementById('api-status');

// Mode elements
const queryModeRadios = document.getElementsByName('query-mode');
const simpleMode = document.getElementById('simple-mode');
const smartMode = document.getElementById('smart-mode');

// Smart mode elements
const smartFileInput = document.getElementById('smart-file-input');
const smartFileName = document.getElementById('smart-file-name');
const smartClearFile = document.getElementById('smart-clear-file');
const smartFilePreview = document.getElementById('smart-file-preview');
const smartRequirements = document.getElementById('smart-requirements');
const smartPreview = document.getElementById('smart-preview');
const smartPreviewText = document.getElementById('smart-preview-text');

let smartFileData = null;
let currentQueryMode = 'simple';

// Check API status on load
checkAPIStatus();

// Event Listeners
submitBtn.addEventListener('click', handleSubmit);
queryInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        handleSubmit();
    }
});

// Mode switcher
queryModeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentQueryMode = e.target.value;
        switchQueryMode(e.target.value);
    });
});

// Smart mode listeners
if (smartFileInput) {
    smartFileInput.addEventListener('change', handleSmartFileSelect);
}
if (smartClearFile) {
    smartClearFile.addEventListener('click', clearSmartFile);
}
if (smartRequirements) {
    smartRequirements.addEventListener('input', updateSmartPreview);
}

// Mode switcher function
function switchQueryMode(mode) {
    if (mode === 'simple') {
        simpleMode.style.display = 'block';
        smartMode.style.display = 'none';
    } else if (mode === 'smart') {
        simpleMode.style.display = 'none';
        smartMode.style.display = 'block';
    }
}

// Check API Status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            apiStatus.textContent = '🟢 Online';
            apiStatus.className = 'status-online';
        } else {
            apiStatus.textContent = '🔴 Offline';
            apiStatus.className = 'status-offline';
        }
    } catch (error) {
        apiStatus.textContent = '🔴 Không kết nối được';
        apiStatus.className = 'status-offline';
    }
}

// Handle Submit
async function handleSubmit() {
    let query;
    
    if (currentQueryMode === 'simple') {
        query = queryInput.value.trim();
    } else if (currentQueryMode === 'smart') {
        query = buildSmartQuery();
    }
    
    if (!query) {
        alert('Vui lòng nhập câu hỏi!');
        return;
    }

    // Show loading state
    setLoadingState(true);
    hideResults();

    const startTime = Date.now();

    try {
        const response = await fetch(`${API_BASE_URL}/agent/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                execute: executeCheckbox.checked
            })
        });

        const endTime = Date.now();
        const duration = ((endTime - startTime) / 1000).toFixed(2);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'API request failed');
        }

        const data = await response.json();
        console.log('[DEBUG] API Response:', data);
        
        displayResults(data, duration);

    } catch (error) {
        console.error('[DEBUG] Error:', error);
        showError(error.message);
    } finally {
        setLoadingState(false);
    }
}

// Display Results
function displayResults(data, duration) {
    try {
        console.log('[DEBUG] displayResults called with:', data);
        resultSection.style.display = 'block';
        
        // Display SQL Query
        const sqlText = data.sql || data.sql_query || 'Không có SQL query';
        console.log('[DEBUG] SQL Text:', sqlText);
        sqlQuery.textContent = sqlText;
        
        // Display execution results if available
        const resultsData = data.result || data.results || [];
        console.log('[DEBUG] Results Data:', resultsData);
        
        if (resultsData && resultsData.length > 0) {
            executionResults.style.display = 'block';
            displayTable(resultsData);
        } else {
            executionResults.style.display = 'none';
        }
        
        // Display error if any
        if (data.error) {
            console.log('[DEBUG] Error in response:', data.error);
            showError(data.error);
            return;
        }
        
        // Update metadata
        responseTime.textContent = `${duration}s`;
        
        // Hide error block if no error
        errorBlock.style.display = 'none';
        
        // Scroll to results
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        console.log('[DEBUG] displayResults completed successfully');
    } catch (err) {
        console.error('[DEBUG] Exception in displayResults:', err);
        throw err;
    }
}

// Display Table
function displayTable(results) {
    if (!results || results.length === 0) {
        tableContainer.innerHTML = '<p>Không có dữ liệu</p>';
        return;
    }

    const headers = Object.keys(results[0]);
    
    let tableHTML = '<table>';
    
    // Table Header
    tableHTML += '<thead><tr>';
    headers.forEach(header => {
        tableHTML += `<th>${escapeHtml(header)}</th>`;
    });
    tableHTML += '</tr></thead>';
    
    // Table Body
    tableHTML += '<tbody>';
    results.forEach(row => {
        tableHTML += '<tr>';
        headers.forEach(header => {
            const value = row[header] === null ? 'NULL' : row[header];
            tableHTML += `<td>${escapeHtml(String(value))}</td>`;
        });
        tableHTML += '</tr>';
    });
    tableHTML += '</tbody>';
    
    tableHTML += '</table>';
    
    tableContainer.innerHTML = tableHTML;
}

// Display Error
function showError(message) {
    resultSection.style.display = 'block';
    errorBlock.style.display = 'block';
    errorMessage.textContent = message;
    
    // Hide other sections
    executionResults.style.display = 'none';
    
    // Scroll to error
    errorBlock.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Hide Results
function hideResults() {
    resultSection.style.display = 'none';
    errorBlock.style.display = 'none';
    executionResults.style.display = 'none';
}

// Set Loading State
function setLoadingState(isLoading) {
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    
    if (isLoading) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';
        submitBtn.disabled = true;
    } else {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// Copy to Clipboard
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        const btn = element.parentElement.querySelector('.copy-btn');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Không thể copy. Vui lòng thử lại!');
    });
}

// Fill Example
function fillExample(card) {
    const exampleText = card.querySelector('p').textContent;
    queryInput.value = exampleText;
    queryInput.focus();
    
    // Scroll to input
    queryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Refresh API status every 30 seconds
setInterval(checkAPIStatus, 30000);

// ==================== SMART QUERY MODE FUNCTIONS ====================

async function handleSmartFileSelect(event) {
    console.log('[SMART] File input changed');
    const file = event.target.files[0];
    if (!file) {
        console.log('[SMART] No file selected');
        return;
    }

    console.log('[SMART] File selected:', file.name, file.type, file.size);
    
    smartFileName.textContent = file.name;
    smartClearFile.style.display = 'inline-block';

    // Show loading message
    smartFilePreview.style.display = 'block';
    smartFilePreview.innerHTML = '<p style="color: #667eea;">⏳ Đang đọc file...</p>';

    try {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        console.log('[SMART] File extension:', fileExtension);
        
        if (fileExtension === 'csv') {
            console.log('[SMART] Reading as CSV...');
            await readSmartCSV(file);
        } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
            console.log('[SMART] Reading as Excel...');
            await readSmartExcel(file);
        } else {
            console.log('[SMART] Unsupported file type');
            alert('Chỉ hỗ trợ file .csv, .xlsx, .xls');
            clearSmartFile();
        }
        console.log('[SMART] File read successfully');
    } catch (error) {
        console.error('[SMART] Error reading file:', error);
        alert('Lỗi đọc file: ' + error.message);
        clearSmartFile();
    }
}

function readSmartCSV(file) {
    return new Promise((resolve, reject) => {
        console.log('[SMART-CSV] Starting to read CSV file');
        const reader = new FileReader();
        
        reader.onload = (e) => {
            try {
                console.log('[SMART-CSV] File loaded, parsing...');
                const text = e.target.result;
                const lines = text.split('\n').filter(line => line.trim());
                
                console.log('[SMART-CSV] Found', lines.length, 'lines');
                
                if (lines.length === 0) {
                    reject(new Error('File CSV rỗng'));
                    return;
                }
                
                const data = lines.map(line => {
                    const fields = [];
                    let current = '';
                    let inQuotes = false;
                    
                    for (let i = 0; i < line.length; i++) {
                        const char = line[i];
                        if (char === '"') {
                            inQuotes = !inQuotes;
                        } else if (char === ',' && !inQuotes) {
                            fields.push(current.trim());
                            current = '';
                        } else {
                            current += char;
                        }
                    }
                    fields.push(current.trim());
                    return fields;
                });
                
                console.log('[SMART-CSV] Parsed data:', data.length, 'rows');
                smartFileData = data;
                displaySmartFilePreview(data, file.name);
                resolve();
            } catch (error) {
                console.error('[SMART-CSV] Parse error:', error);
                reject(error);
            }
        };
        
        reader.onerror = () => {
            console.error('[SMART-CSV] FileReader error');
            reject(new Error('Không thể đọc file'));
        };
        reader.readAsText(file);
    });
}

function readSmartExcel(file) {
    return new Promise((resolve, reject) => {
        console.log('[SMART-EXCEL] Starting to read Excel file');
        
        // Check if XLSX library is loaded
        if (typeof XLSX === 'undefined') {
            console.error('[SMART-EXCEL] XLSX library not loaded!');
            reject(new Error('Thư viện đọc Excel chưa được tải. Vui lòng refresh trang.'));
            return;
        }
        
        const reader = new FileReader();
        
        reader.onload = (e) => {
            try {
                console.log('[SMART-EXCEL] File loaded, parsing...');
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                
                console.log('[SMART-EXCEL] Workbook loaded, sheets:', workbook.SheetNames);
                
                const firstSheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheetName];
                const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
                
                console.log('[SMART-EXCEL] Parsed data:', jsonData.length, 'rows');
                
                if (jsonData.length === 0) {
                    reject(new Error('Sheet Excel rỗng'));
                    return;
                }
                
                smartFileData = jsonData;
                displaySmartFilePreview(jsonData, file.name);
                resolve();
            } catch (error) {
                console.error('[SMART-EXCEL] Parse error:', error);
                reject(error);
            }
        };
        
        reader.onerror = () => {
            console.error('[SMART-EXCEL] FileReader error');
            reject(new Error('Không thể đọc file'));
        };
        reader.readAsArrayBuffer(file);
    });
}

function displaySmartFilePreview(data, filename) {
    console.log('[SMART-PREVIEW] Displaying preview for:', filename, 'with', data.length, 'rows');
    
    if (!data || data.length === 0) {
        console.error('[SMART-PREVIEW] No data to display');
        return;
    }
    
    // Rebuild the preview HTML
    smartFilePreview.style.display = 'block';
    smartFilePreview.innerHTML = `
        <p><strong>📄 File:</strong> <span id="smart-file-info-name">${escapeHtml(filename)}</span></p>
        <p><strong>📊 Số dòng dữ liệu:</strong> <span id="smart-file-info-rows">${data.length - 1} dòng</span></p>
        <p>
            <strong>📌 Cột chứa mã tra cứu:</strong>
            <select id="smart-column-select" class="column-select"></select>
        </p>
        <div id="smart-data-preview" class="data-preview-mini"></div>
        <p style="color: #27ae60; font-weight: 600; margin-top: 10px;">✅ File đã được tải thành công!</p>
    `;
    
    // Get new references after innerHTML change
    const newSmartColumnSelect = document.getElementById('smart-column-select');
    const newSmartDataPreview = document.getElementById('smart-data-preview');
    
    // Populate column select
    const headers = data[0];
    console.log('[SMART-PREVIEW] Headers:', headers);
    
    newSmartColumnSelect.innerHTML = '';
    headers.forEach((header, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = header || `Cột ${index + 1}`;
        newSmartColumnSelect.appendChild(option);
    });
    
    // Re-attach change listener
    newSmartColumnSelect.addEventListener('change', updateSmartPreview);
    
    // Show data preview (first 5 values)
    const columnIndex = 0;
    const previewValues = data
        .slice(1, 6)
        .map(row => row[columnIndex])
        .filter(val => val !== undefined && val !== null && val !== '');
    
    newSmartDataPreview.textContent = `Ví dụ: ${previewValues.join(', ')}...`;
    
    console.log('[SMART-PREVIEW] Preview displayed successfully');
    
    // Update preview
    updateSmartPreview();
}

function updateSmartPreview() {
    if (!smartFileData || !smartRequirements.value.trim()) {
        smartPreview.style.display = 'none';
        return;
    }
    
    const query = buildSmartQuery();
    if (query) {
        smartPreview.style.display = 'block';
        smartPreviewText.textContent = query;
    }
}

function buildSmartQuery() {
    if (!smartFileData || smartFileData.length < 2) {
        return null;
    }
    
    const requirements = smartRequirements.value.trim();
    if (!requirements) {
        return null;
    }
    
    const columnSelectElem = document.getElementById('smart-column-select');
    const columnIndex = columnSelectElem ? parseInt(columnSelectElem.value) : 0;
    const columnData = smartFileData
        .slice(1)
        .map(row => row[columnIndex])
        .filter(val => val !== undefined && val !== null && val !== '');
    
    if (columnData.length === 0) {
        return null;
    }
    
    // Build query
    const dataList = columnData.join('; ');
    const columnName = smartFileData[0][columnIndex] || 'mã tra cứu';
    
    const query = `${requirements}\n\nDanh sách ${columnName}: ${dataList}`;
    
    return query;
}

function clearSmartFile() {
    smartFileInput.value = '';
    smartFileName.textContent = '';
    smartClearFile.style.display = 'none';
    smartFilePreview.style.display = 'none';
    smartFileData = null;
    smartPreview.style.display = 'none';
}
