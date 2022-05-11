// Displays edit box 
function edit(post_id) {
    document.querySelector(`#edit-${post_id}`).style.display = "block";
}

// Updates post after editing
function update(post_id) {
    const updated = document.querySelector(`#form-${post_id}`).value;

    // Calls the post API to update the body of the post
    fetch(`/post/${post_id}`, {
        method: "POST",
        body: JSON.stringify({
            body: updated
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });

    document.querySelector(`#body-${post_id}`).innerHTML = updated;
    document.querySelector(`#edit-${post_id}`).style.display = "none";
    return false;
}
  
// Updates the like count
function like(like_id) {
    const likeBtn = document.querySelector(`#like-btn-${like_id}`);
    const likeCount = document.querySelector(`#like-count-${like_id}`);

    // Calls the like API
    fetch(`/like/${like_id}`)
    .then(response => response.json())
    .then(post => {
        console.log(post);
        let count = post.likes;

        // If the post is not liked, like the post 
        if (likeBtn.style.color === "black") {
            fetch(`/like/${like_id}`, {
                method: "PUT",
                body: JSON.stringify({
                    likes: true,
                })
            });

            likeBtn.style.color = "olivedrab";
            likeCount.innerHTML = ++count;

        // If the post is liked, remove the like
        } else {
            fetch(`/like/${like_id}`, {
                method: "PUT",
                body: JSON.stringify({
                    likes: false,
                })
            });

            likeBtn.style.color = "black";
            likeCount.innerHTML = --count;
        }
    });
}