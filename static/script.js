// Handle adding tasks without page refresh
const addForm = document.getElementById("addTaskForm");

if (addForm) {
    addForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const taskName = e.target.task_name.value;

        fetch('/add_task', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: taskName})
        })
        .then(response => response.json())
        .then(data => {
            if (data.task) {
                const taskList = document.getElementById('taskList');
                const li = document.createElement('li');
                li.textContent = data.task.name;
                taskList.appendChild(li);
                e.target.task_name.value = '';
            }
        });
    });
}

function closeModal() {
    document.getElementById("editModal").style.display = "none";
}

document.addEventListener("DOMContentLoaded", function() {
    // Close modal
    function closeModal() {
        document.getElementById("editModal").style.display = "none";
    }

    // Open modal with task info
    document.querySelectorAll(".editButton").forEach(button => {
        button.addEventListener("click", function() {
            document.getElementById("editTaskId").value = this.dataset.id;
            document.getElementById("editTaskName").value = this.dataset.name;
            document.getElementById("editTaskDescription").value = this.dataset.description || "";
            document.getElementById("editTaskClass").value = this.dataset.course || "";
            document.getElementById("editTaskDueDate").value = this.dataset.dueDate;
            document.getElementById("editTaskPriority").value = this.dataset.priority;
            document.getElementById("editTaskStatus").value = this.dataset.status;

            document.getElementById("editModal").style.display = "block";
        });
    });

    // Handle submit changes
    document.getElementById("editTaskForm").addEventListener("submit", function(e) {
        e.preventDefault();

        const id = document.getElementById("editTaskId").value;
        const payload = {
            name: document.getElementById("editTaskName").value,
            description: document.getElementById("editTaskDescription").value,
            course: document.getElementById("editTaskClass").value,
            due_date: document.getElementById("editTaskDueDate").value,
            priority: document.getElementById("editTaskPriority").value,
            status: document.getElementById("editTaskStatus").value
        };

        fetch(`/edit_task/${id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            // Close modal
            closeModal();

            // Update task row dynamically
            const row = document.getElementById(`task-${id}`);
            if (!row) return;

            row.querySelector(".task-cell.name").textContent = payload.name;
            row.querySelector(".task-cell.description").textContent = payload.description;
            row.querySelector(".task-cell.class").textContent = payload.course;

            // Format due date as "Mar 09, 2026"
            if (payload.due_date) {
                const [year, month, day] = payload.due_date.split("-");
                const formattedDate = new Date(year, month - 1, day);
                row.querySelector(".task-cell.due").textContent =
                    formattedDate.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" });
            }

            row.querySelector(".task-cell.priority").textContent = payload.priority;
            row.querySelector(".task-cell.status").textContent = payload.status;

            // Update edit button dataset
            const editBtn = row.querySelector(".editButton");
            editBtn.dataset.name = payload.name;
            editBtn.dataset.description = payload.description;
            editBtn.dataset.course = payload.course;
            editBtn.dataset.dueDate = payload.due_date;
            editBtn.dataset.priority = payload.priority;
            editBtn.dataset.status = payload.status;

            // Update row color class
            row.className = `task-row priority-${payload.priority}`;
        })
        .catch(err => {
            console.error("Edit failed:", err);
            closeModal();
        });
    });

    // Close button inside modal
    document.querySelector("#editModal button[type='button']").addEventListener("click", closeModal);
});

const calendarGrid = document.getElementById("calendarGrid");
const monthYear = document.getElementById("monthYear");

let currentDate = new Date();

function renderCalendar(date) {
    calendarGrid.innerHTML = "";

    const year = date.getFullYear();
    const month = date.getMonth();
    const today = new Date();

    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();

    const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    monthYear.textContent = `${monthNames[month]} ${year}`;

    const daysOfWeek = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    daysOfWeek.forEach(day => {
        const dayDiv = document.createElement("div");
        dayDiv.classList.add("day-name");
        dayDiv.textContent = day;
        calendarGrid.appendChild(dayDiv);
    });

    for (let i = 0; i < firstDay; i++) {
        calendarGrid.appendChild(document.createElement("div"));
    }

    for (let day = 1; day <= lastDate; day++) {
        const dayDiv = document.createElement("div");
        dayDiv.classList.add("day");

        // Day number
        const dateNumber = document.createElement("div");
        dateNumber.textContent = day;
        dayDiv.appendChild(dateNumber);

        // Tasks for this day
        calendarTasks.forEach(task => {
            if (!task.due_date || task.status === "Completed") return;

            const dueDate = new Date(task.due_date + "T00:00:00");

            if (dueDate.getDate() === day &&
                dueDate.getMonth() === month &&
                dueDate.getFullYear() === year) {

                const taskBox = document.createElement("div");
                taskBox.classList.add("task-box");
                taskBox.textContent = task.name;

                //Automatic color-coded system
                const course = (task.course || "").toLowerCase().trim();

                if (
                    course.includes("science") || 
                    course.includes("biology") || 
                    course.includes("chemistry") || 
                    course.includes("physics")
                ) {
                    taskBox.classList.add("science-task");
                } 
                else if (
                    course.includes("math") || 
                    course.includes("algebra") || 
                    course.includes("calculas") || 
                    course.includes("equations") || 
                    course.includes("cryptology") || 
                    course.includes("statistics")
                ) {
                    taskBox.classList.add("math-task");
                } 
                else if (
                    course.includes("english") || 
                    course.includes("writing") || 
                    course.includes("reading") || 
                    course.includes("journaling")
                ) {
                    taskBox.classList.add("english-task");
                } 
                else if (
                    course.includes("history") || 
                    course.includes("culture") || 
                    course.includes("culinary") || 
                    course.includes("philosophy") || 
                    course.includes("theology")
                ) {
                    taskBox.classList.add("humanities-task");
                } 
                else if (
                    course.includes("spanish") || 
                    course.includes("german") || 
                    course.includes("italian") || 
                    course.includes("french") || 
                    course.includes("russian") || 
                    course.includes("mandarin") || 
                    course.includes("japanese") || 
                    course.includes("korean")
                ) {
                    taskBox.classList.add("language-task");
                } 
                else {
                    taskBox.classList.add("default-task");
                }

                taskBox.dataset.taskId = task.id;

                taskBox.addEventListener("click", () => {
                    const taskId = taskBox.dataset.taskId;
                    const t = calendarTasks.find(x => x.id == taskId);
                    if (!t) return;

                    document.getElementById("modalTaskName").textContent = t.name;
                    document.getElementById("modalDescription").textContent = t.description;
                    document.getElementById("modalCourse").textContent = t.course;
                    document.getElementById("modalDueDate").textContent = t.due_date;
                    document.getElementById("modalPriority").textContent = t.priority || "N/A";
                    document.getElementById("modalStatus").value = t.status || "Not Started";
                    document.getElementById("saveStatusBtn").dataset.taskId = t.id;

                    document.getElementById("taskModal").style.display = "block";
                });

                dayDiv.appendChild(taskBox);
            }
        });

        if (day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear()) {
            dayDiv.classList.add("today");
        }

        calendarGrid.appendChild(dayDiv);
    }
}

function goToPreviousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar(currentDate);
}

function goToNextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar(currentDate);
}

document.addEventListener("DOMContentLoaded", function() {
    // Close modal
    document.querySelector(".modal .close").onclick = () => {
        document.getElementById("taskModal").style.display = "none";
    };
    window.onclick = (event) => {
        if (event.target.id === "taskModal") {
            document.getElementById("taskModal").style.display = "none";
        }
    };

    // Save status button
    document.getElementById("saveStatusBtn").addEventListener("click", () => {
        const taskId = document.getElementById("saveStatusBtn").dataset.taskId;
        const newStatus = document.getElementById("modalStatus").value;

        fetch(`/update_task_status/${taskId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Status updated!");
                document.getElementById("taskModal").style.display = "none";
                renderCalendar(currentDate); // Refresh calendar
            } else {
                alert("Error updating status.");
            }
        });
    });

    renderCalendar(currentDate); // Make sure calendar renders after DOM is ready
});

document.getElementById("saveStatusBtn").addEventListener("click", () => {
    const taskId = document.getElementById("saveStatusBtn").dataset.taskId;
    const newStatus = document.getElementById("modalStatus").value;

    fetch(`/update_task_status/${taskId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Status updated!");
            document.getElementById("taskModal").style.display = "none";
            renderCalendar(currentDate); // Refresh calendar to reflect changes
        } else {
            alert("Error updating status.");
        }
    });
});

function openMenu() {
    document.getElementById("sideMenu").style.width = "250px";
    document.getElementById("overlay").style.width = "100%";
  }

function closeMenu() {
document.getElementById("sideMenu").style.width = "0";
document.getElementById("overlay").style.width = "0";
}