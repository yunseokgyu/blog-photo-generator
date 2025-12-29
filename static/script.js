const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const processBtn = document.getElementById('process-btn');
const statusArea = document.getElementById('status-area');
const resultArea = document.getElementById('result-area');
const downloadLink = document.getElementById('download-link');

let selectedFiles = [];

// Drag & Drop events
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
});

dropZone.addEventListener('drop', handleDrop, false);
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFiles);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles({ target: { files: files } });
}

function handleFiles(e) {
    const newFiles = [...e.target.files];
    selectedFiles = [...selectedFiles, ...newFiles];
    updateFileList();
}

function updateFileList() {
    if (selectedFiles.length > 0) {
        fileList.textContent = `${selectedFiles.length}개의 파일이 선택됨: ` +
            selectedFiles.map(f => f.name).join(', ');
        processBtn.disabled = false;
    } else {
        fileList.textContent = '';
        processBtn.disabled = true;
    }
}

processBtn.addEventListener('click', uploadAndProcess);

function uploadAndProcess() {
    const keywords = document.getElementById('keywords').value;
    const targetCount = document.getElementById('target-count').value;

    if (!keywords) {
        alert('키워드를 입력해주세요!');
        return;
    }

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });
    formData.append('keywords', keywords);
    formData.append('target_count', targetCount);

    processBtn.disabled = true;
    statusArea.classList.remove('hidden');
    resultArea.classList.add('hidden');

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('Upload failed');
            return response.json();
        })
        .then(data => {
            statusArea.classList.add('hidden');
            resultArea.classList.remove('hidden');
            downloadLink.href = data.download_url;
            selectedFiles = []; // Reset
            updateFileList();
        })
        .catch(error => {
            console.error('Error:', error);
            statusArea.classList.add('hidden');
            alert('처리 중 오류가 발생했습니다.');
            processBtn.disabled = false;
        });
}

// Comparison Logic
const dropA = document.getElementById('drop-a');
const inputA = document.getElementById('input-a');
const dropB = document.getElementById('drop-b');
const inputB = document.getElementById('input-b');
const compareBtn = document.getElementById('compare-btn');
let fileA = null;
let fileB = null;

// Helpers for comparison drops
function setupMiniDrop(drop, input, setFileCallback) {
    drop.addEventListener('click', () => input.click());
    input.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            setFileCallback(e.target.files[0]);
            drop.style.borderColor = '#28a745';
            drop.style.background = '#e6ffec';
            drop.innerHTML = `✅ ${e.target.files[0].name}`;
        }
    });
    drop.addEventListener('dragover', (e) => {
        e.preventDefault();
        drop.style.borderColor = 'var(--primary)';
    });
    drop.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files[0]) {
            setFileCallback(e.dataTransfer.files[0]);
            drop.style.borderColor = '#28a745';
            drop.style.background = '#e6ffec';
            drop.innerHTML = `✅ ${e.dataTransfer.files[0].name}`;
        }
    });
}

if (dropA && dropB) {
    setupMiniDrop(dropA, inputA, (f) => fileA = f);
    setupMiniDrop(dropB, inputB, (f) => fileB = f);

    compareBtn.addEventListener('click', () => {
        if (!fileA || !fileB) {
            alert("비교할 두 이미지를 모두 올려주세요 (A:원본, B:세탁본)");
            return;
        }

        const formData = new FormData();
        formData.append('fileA', fileA);
        formData.append('fileB', fileB);

        compareBtn.textContent = "분석 중...";
        compareBtn.disabled = true;

        fetch('/compare', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                document.getElementById('compare-result').classList.remove('hidden');
                document.getElementById('res-meta-a').textContent = data.metaA;
                document.getElementById('res-meta-b').textContent = data.metaB;
                document.getElementById('res-size-a').textContent = data.sizeA;
                document.getElementById('res-size-b').textContent = data.sizeB;
                document.getElementById('res-dim-a').textContent = data.dimA;
                document.getElementById('res-dim-b').textContent = data.dimB;
                document.getElementById('diff-image').src = data.diffImage;

                compareBtn.textContent = "🔍 비교 분석 시작";
                compareBtn.disabled = false;
            })
            .catch(err => {
                console.error(err);
                alert("분석 중 오류가 발생했습니다.");
                compareBtn.textContent = "🔍 비교 분석 시작";
                compareBtn.disabled = false;
            });
    });
}
