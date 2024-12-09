// Functions related to query handling
function clearQuery() {
    // Clear the textarea
    document.getElementById('query').value = '';
}

function clearQueryAndReset() {
    // trigger the form reset
    document.getElementById('search-form').reset();
    // then clear the query
    clearQuery();
}

// Functions related to article body toggling
function toggleArticleBody(button) {
    const articleBody = button.closest('.article').querySelector('.article-body');
    if (articleBody.style.display === "none" || articleBody.style.display === "") {
        articleBody.style.display = "block";
        button.textContent = "Collapse";
    } else {
        articleBody.style.display = "none";
        button.textContent = "Expand";
    }
}

function expandAllArticles() {
    document.querySelectorAll('.article-body').forEach(body => {
        body.style.display = 'block';
    });
    document.querySelectorAll('.btn-toggle').forEach(button => {
        button.textContent = 'Collapse';
    });
}

function collapseAllArticles() {
    document.querySelectorAll('.article-body').forEach(body => {
        body.style.display = 'none';
    });
    document.querySelectorAll('.btn-toggle').forEach(button => {
        button.textContent = 'Expand';
    });
}
