// 전역 변수로 이동
let selectedAvatar = null;  
let mainProfileImage = null;
let navProfileImage = null;

document.addEventListener("DOMContentLoaded", function () {
    // DOM 요소 초기화
    const avatarOptions = document.querySelectorAll(".avatar-option img");
    mainProfileImage = document.getElementById("mainProfileImage");
    navProfileImage = document.getElementById("navProfileImage");

    // 아바타 옵션 클릭 이벤트 등록
    avatarOptions.forEach((avatar, index) => {
        avatar.addEventListener("click", function () {
            selectedAvatar = index + 2;  // 2, 3, 4, 5 중 하나의 값
            
            // 선택된 아바타 강조 표시
            avatarOptions.forEach(opt => opt.classList.remove("selected"));
            avatar.classList.add("selected");

            // 메인 프로필 이미지 미리보기 업데이트
            mainProfileImage.src = avatar.src;
        });
    });
});

// 프로필 이미지 변경 서버 요청
function saveAvatar() {
    if (selectedAvatar === null) {
        alert("프로필 이미지를 선택해주세요.");
        return;
    }

    // 서버로 변경 요청 전송
    fetch('/common/update-profile-image/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ image_id: selectedAvatar })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 새로운 이미지 URL에 타임스탬프 추가 (캐시 방지용)
            const newImageUrl = data.new_image_url + '?t=' + new Date().getTime();
            updateProfileImages(newImageUrl);
            alert("프로필 이미지가 성공적으로 변경되었습니다.");
        } else {
            alert("프로필 이미지 변경 중 오류가 발생했습니다.");
            console.error("오류:", data.error);
        }
    })
    .catch(error => console.error("오류 발생:", error));
}

// 프로필 이미지 업데이트 함수
function updateProfileImages(newImageUrl) {
    // 메인 프로필 이미지 업데이트
    if (mainProfileImage) {
        mainProfileImage.src = newImageUrl;
    }

    // 네비게이션 바의 프로필 이미지 업데이트
    if (navProfileImage) {
        navProfileImage.src = newImageUrl;
    }
}

// CSRF 토큰 함수
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split("; ");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].split("=");
            if (cookie[0] === name) {
                cookieValue = decodeURIComponent(cookie[1]);
                break;
            }
        }
    }
    return cookieValue;
}
