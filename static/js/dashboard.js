console.log('Dashboard.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    loadPage(1);

    const paginationElement = document.getElementById('pagination');
    if (paginationElement) {
        paginationElement.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                e.preventDefault();
                const page = e.target.getAttribute('data-page');
                console.log('Pagination clicked, loading page:', page);
                loadPage(page);
            }
        });
    } else {
        console.error('Pagination element not found');
    }

    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Filter form submitted');
            loadPage(1);
        });
    } else {
        console.error('Filter form not found');
    }
});

function loadPage(page) {
    console.log('loadPage function called with page:', page);
    const loading = document.getElementById('loading');
    const container = document.getElementById('voucher-table-container');
    const filterForm = document.getElementById('filter-form');

    if (!loading || !container || !filterForm) {
        console.error('Required elements not found');
        return;
    }

    const formData = new FormData(filterForm);
    formData.append('page', page);

    console.log('Form data:', Object.fromEntries(formData));

    loading.style.display = 'block';

    const url = '/painel/?' + new URLSearchParams(formData);
    console.log('Fetching URL:', url);

    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Received data:', data);
        if (data.html) {
            container.innerHTML = data.html;
            if (data.pagination) {
                updatePagination(data.pagination);
            } else {
                console.error('No pagination data in the response');
            }
        } else {
            console.error('No HTML content in the response');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })
    .finally(() => {
        loading.style.display = 'none';
    });
}

function updatePagination(paginationData) {
    console.log('Updating pagination with data:', paginationData);
    const paginationElement = document.getElementById('pagination');
    let paginationHtml = '';

    if (paginationData.has_previous) {
        paginationHtml += `<li class="page-item">
            <a class="page-link" href="#" data-page="${paginationData.previous_page_number}" aria-label="Anterior">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>`;
    }

    for (let i = paginationData.page_range[0]; i <= paginationData.page_range[1]; i++) {
        if (i === paginationData.current_page) {
            paginationHtml += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
    }

    if (paginationData.has_next) {
        paginationHtml += `<li class="page-item">
            <a class="page-link" href="#" data-page="${paginationData.next_page_number}" aria-label="Próximo">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>`;
    }

    paginationElement.innerHTML = paginationHtml;
}