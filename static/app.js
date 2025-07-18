//FOR AMBIENT LIGHT
var video = document.getElementById("video");
var canvas = document.getElementById("canvas");
var ctx = canvas.getContext("2d");

canvas.style.width = video.clientWidth + "px";
canvas.style.height = video.clientHeight + "px";

id = setInterval(getCurrentImage, 100);
function getCurrentImage() {
  if (video.src != null) {
    canvas.style.width = video.clientWidth + "px";
    canvas.style.height = video.clientHeight + "px";
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  } else {
    clearInterval(id);
  }
}

//FOR AMBIENT LIGHT END

let generatePlaylistBtn = document.getElementById("generateButton");
loader = document.getElementById("loader");
generatePlaylistBtn.addEventListener("click", handleGeneratePlaylistClick);

async function handleGeneratePlaylistClick() {
  console.log("button clicked");
  loader.style.display = "block";
  generatePlaylistBtn.style.display = "none";
  let data = await fetchPlaylist();
  displayPlaylist(data);
}
function changeEmojiTo(emotion) {
  emojiset = {
    angry: "",
    happy: "",
    sad: "",
    fearful: "",
    disgusted: "",
    surprised: "",
    neutral: "",
  };
  let emoji = emojiset[emotion.toLowerCase()];
  let encoded_emoji = encodeURI(emoji);
  let emoji_bg = document.querySelector(".emoji-background");
  emoji_bg.style.backgroundImage = `url(
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='50' viewBox='0 0 64 64'%3E%3Ctext y='50%25' x='40%25' dy='0.35em' text-anchor='middle' style='font-size:41px;'%3E${encoded_emoji}%3C/text%3E%3C/svg%3E"
  )`;
}
function fetchPlaylist() {
  return fetch("/get_recommendations")
    .then((response) => response.text()) // Get the response as text
    .then((text) => {
      // Attempt custom parsing or replacement here
      const safeText = text.replace(/NaN/g, "null"); // Example: replacing 'NaN' with 'null'
      return JSON.parse(safeText);
    })
    .catch((err) => console.log(err));
}

//fetch songs and display them
let videoPage = document.querySelector(".camera-container");
let playlistpage = document.querySelector(".playlist-container");
let emotionDisplay = document.getElementById("detected-emotion");
let playing_audios = [];

displayPlaylist = (data) => {
  video.src = null;
  lastDetectedEmotion = data.detected_emotion;
  emotionDisplay.textContent =
    data.detected_emotion === "neutral" ? "No Face detected" : data.detected_emotion;
  changeEmojiTo(data.detected_emotion);

  const table = document.getElementById("playlist-table");
  const videoPage = document.querySelector(".camera-container");
  const playlistpage = document.querySelector(".playlist-container");
  const languageFilter = document.getElementById("languageFilter");

  videoPage.style.display = "none";
  playlistpage.style.display = "block";

  // ✅ Normalize language for each track
  let allTracks = data.music_data.map((track) => {
    track.language = track.language?.toLowerCase().trim() || "unknown";
    return track;
  });

  function renderFilteredTracks() {
    table.querySelector("tbody").innerHTML = "";

    const selectedLanguage = languageFilter?.value || "all";

    console.log("Available Languages:", [...new Set(allTracks.map(t => t.language))]);
    console.log("Selected Language:", selectedLanguage);

    const filteredTracks =
      selectedLanguage === "all"
        ? allTracks
        : allTracks.filter(
            (track) => track.language === selectedLanguage.toLowerCase().trim()
          );

    filteredTracks.forEach((music, index) => {
      let datarow = document.createElement("tr");
      datarow.className = "playlist-row mt-1 mb-1";

      const playCell = document.createElement("td");

const playBtn = document.createElement("a");
playBtn.href = music.SpotifyURL;
playBtn.target = "_blank";  // open in new tab
playBtn.className = "btn btn-success btn-sm d-flex align-items-center gap-1";
playBtn.style = "padding: 0.4rem 0.6rem; font-size: 0.85rem; width: fit-content;";
playBtn.innerHTML = `
  <img src="https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg" 
       alt="Spotify" style="width: 16px; height: 16px;" />
  <span>Play</span>
`;

playBtn.addEventListener("click", () => {
   logAndRedirect(music, lastDetectedEmotion);  // only logs, does not block navigation
});



playCell.appendChild(playBtn);



      const nameCell = document.createElement("td");
      nameCell.textContent = music.Name;

      let covercell = document.createElement("td");
      let cover = document.createElement("img");
      cover.src = music.Image;
      cover.style.width = "70px";
      cover.style.height = "70px";
      cover.style.borderRadius = "50%";
      covercell.appendChild(cover);

      const artistCell = document.createElement("td");
      artistCell.textContent = music.Artist;

      const albumCell = document.createElement("td");
      albumCell.textContent = music.Album;

      const langCell = document.createElement("td");
      langCell.textContent = music.language || "-";

      const indexCell = document.createElement("td");
      indexCell.textContent = index + 1;

      datarow.appendChild(indexCell);
      datarow.appendChild(playCell);
      datarow.appendChild(covercell);
      datarow.appendChild(nameCell);
      datarow.appendChild(artistCell);
      datarow.appendChild(albumCell);
      datarow.appendChild(langCell);

      table.querySelector("tbody").appendChild(datarow);
    });
  }

  if (languageFilter) {
    languageFilter.removeEventListener("change", renderFilteredTracks); // avoid duplicate listener
    languageFilter.addEventListener("change", renderFilteredTracks);
  }

  renderFilteredTracks(); // Initial render
};

let shuffleButton = document.getElementById("shuffleButton");
if (shuffleButton) {
  shuffleButton.addEventListener("click", handleShuffleClick);
}

function fetchPlaylist(isShuffle = false) {
  const url = isShuffle ? "/get_recommendations?shuffle=1" : "/get_recommendations";
  return fetch(url)
    .then((response) => response.text())
    .then((text) => {
      const safeText = text.replace(/NaN/g, "null");
      return JSON.parse(safeText);
    })
    .catch((err) => console.log(err));
}


async function handleShuffleClick() {
  console.log("Shuffling songs...");
  loader.style.display = "block";
  shuffleButton.disabled = true;

  const data = await fetchPlaylist(true); // <-- use shuffle flag
  displayPlaylist(data);

  loader.style.display = "none";
  shuffleButton.disabled = false;
}

 