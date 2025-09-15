document.addEventListener('DOMContentLoaded', function() {
    // Fetch and display active users
    fetchActiveUsers();

    // Set up polling to update user list periodically
    setInterval(fetchActiveUsers, 30000); // Update every 30 seconds
});

function fetchActiveUsers() {
    fetch('/oauth2/active-users')
        .then(response => response.json())
        .then(data => {
            updateUsersList(data.users);
        })
        .catch(error => console.error('Error fetching users:', error));
}

function updateUsersList(users) {
    const usersList = document.getElementById('usersList');
    usersList.innerHTML = '';

    users.forEach(user => {
        const userElement = createUserElement(user);
        usersList.appendChild(userElement);
    });
}

function createUserElement(user) {
    const userItem = document.createElement('div');
    userItem.className = 'user-item';
    
    userItem.innerHTML = `
        <img class="user-avatar" src="${user.picture}" alt="User avatar">
        <div class="user-info">
            <div class="user-name">${user.name}</div>
            <div class="user-email">${user.email}</div>
        </div>
        <button class="logout-btn" onclick="logoutUser('${user.id}')">Logout</button>
    `;
    
    return userItem;
}

function logoutUser(userId) {
    fetch(`/oauth2/logout/${userId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetchActiveUsers(); // Refresh the user list
        } else {
            alert('Logout failed: ' + data.message);
        }
    })
    .catch(error => console.error('Error logging out:', error));
}