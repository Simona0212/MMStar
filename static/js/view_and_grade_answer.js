// static/js/view_and_grade_answer.js

document.addEventListener('DOMContentLoaded', function () {
    const importBtn = document.getElementById('import-ai-feedback-btn');
    if (importBtn) {
        importBtn.addEventListener('click', function () {
            // 获取 course_id、question_id 和 answer_id
            const course_id = JSON.parse(document.getElementById('course-id').textContent);
            const question_id = JSON.parse(document.getElementById('question-id').textContent);
            const answer_id = JSON.parse(document.getElementById('answer-id').textContent);

            // 发送 AJAX 请求获取 AI 评分与反馈
            fetch(`/teacher_course/${course_id}/question/${question_id}/answer/${answer_id}/import_ai_feedback/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // 填充表单
                    document.getElementById('id_Score').value = data.data.score;
                    document.getElementById('id_Feedback').value = data.data.feedback;
                    alert('已成功导入当前评价。');
                } else {
                    alert(`导入失败：${data.message}`);
                }
            })
            .catch(error => {
                console.error('错误:', error);
                alert('导入当前评价过程中发生错误。');
            });
        });
    }
});

// 辅助函数：获取指定名称的 Cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            // 判断 Cookie 是否以指定名称开头
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}