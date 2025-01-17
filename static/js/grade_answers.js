// static/js/grade_answers.js

document.addEventListener('DOMContentLoaded', function () {
    // 获取 course_id 和 question_id
    const course_id = JSON.parse(document.getElementById('course-id').textContent);
    const question_id = JSON.parse(document.getElementById('question-id').textContent);

    // // 选择所有答案
    document.getElementById('select-all-answers').addEventListener('change', function () {
        let checkboxes = document.querySelectorAll('.answer-checkbox');
        checkboxes.forEach(cb => cb.checked = this.checked);
    });

    // 批量智能评分按钮点击事件
    document.getElementById('batch-grade-btn').addEventListener('click', function () {
        let selectedCheckboxes = Array.from(document.querySelectorAll('.answer-checkbox:checked'));
        let selectedAnswers = selectedCheckboxes.map(cb => cb.value);
        let modelChoice = document.getElementById('model_choice').value;

        if (selectedAnswers.length === 0) {
            alert('请选择至少一个学生答案进行评分。');
            return;
        }

        if (!modelChoice) {
            alert('请选择一个可用的大模型进行评分。');
            return;
        }

        if (!confirm(`确定使用选择的大模型进行批量智能评分吗？`)) {
            return;
        }

        // 禁用按钮以防止重复提交
        this.disabled = true;
        this.innerText = '评分中...';

        // 创建 URLSearchParams 实例并正确添加多个 'answer_ids[]'
        let params = new URLSearchParams();
        selectedAnswers.forEach(id => params.append('answer_ids[]', id));
        params.append('model_choice', modelChoice);  // 这里传递的是 API Key 的 ID

        // 发送 AJAX 请求进行批量评分
        fetch(`/teacher_course/${course_id}/question/${question_id}/batch_ai_grade/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken'),  // 获取 CSRF Token
            },
            // body: new URLSearchParams({
            //     'answer_ids[]': selectedAnswers,
            //     'model_choice': modelChoice,  // 这里传递的是 API Key 的 ID
            // })
            body: params.toString()
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 遍历评分结果并更新界面上的评价状态
                for (let answer_id in data.results) {
                    let row = document.getElementById(`row-${answer_id}`);
                    if (row) {
                        let statusCell = row.querySelector('td:nth-child(6)');
                        let feedback = data.results[answer_id];
                        if (feedback.status === 'success') {
                            statusCell.innerHTML = '<span class="badge bg-success">✅ 已评价</span>';
                        } else if (feedback.status === 'error') {
                            statusCell.innerHTML = `<span class="badge bg-warning">⚠️ ${feedback.message}</span>`;
                        } else {
                            statusCell.innerHTML = '<span class="badge bg-secondary">❌ 未评价</span>';
                        }
                    }
                }

                alert('批量智能评分完成。');
            } else {
                alert(`批量智能评分失败：${data.message}`);
            }

            // 重置按钮状态
            let batchBtn = document.getElementById('batch-grade-btn');
            batchBtn.disabled = false;
            batchBtn.innerText = '批量智能评分';
        })
        .catch(error => {
            console.error('错误:', error);
            alert('批量智能评分过程中发生错误。');

            // 重置按钮状态
            let batchBtn = document.getElementById('batch-grade-btn');
            batchBtn.disabled = false;
            batchBtn.innerText = '批量智能评分';
        });
    });
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