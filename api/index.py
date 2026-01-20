from flask import Flask, jsonify, request, render_template, Response, stream_with_context
import requests
import json
import base64
import random
import time

app = Flask(__name__)

# --- KONFIGURASI ---
API_HOST = "https://api.tmtreader.com"

# Headers Default
head = {
    "Host": "api.tmtreader.com",
    "Accept": "application/json; charset=utf-8,application/x-protobuf",
    "X-Xs-From-Web": "false",
    "Age-Range": "8",
    "Sdk-Version": "2",
    "Passport-Sdk-Version": "50357",
    "X-Vc-Bdturing-Sdk-Version": "2.2.1.i18n",
    "User-Agent": "com.worldance.drama/49819 (Linux; U; Android 9; in; SM-N976N; Build/QP1A.190711.020;tt-ok/3.12.13.17)",
}

# Params Default
params = {
    "iid": "7549249992780367617",
    "device_id": "6944790948585719298",
    "ac": "wifi",
    "channel": "gp",
    "aid": "645713",
    "app_name": "Melolo",
    "version_code": "49819",
    "version_name": "4.9.8",
    "device_platform": "android",
    "os": "android",
    "ssmix": "a",
    "device_type": "SM-N976N",
    "device_brand": "samsung",
    "language": "in",
    "os_api": "28",
    "os_version": "9",
    "openudid": "707e4ef289dcc394",
    "manifest_version_code": "49819",
    "resolution": "900*1600",
    "dpi": "320",
    "update_version_code": "49819",
    "current_region": "ID",
    "carrier_region": "ID",
    "app_language": "id",
    "sys_language": "in",
    "app_region": "ID",
    "sys_region": "ID",
    "mcc_mnc": "46002",
    "carrier_region_v2": "460",
    "user_language": "id",
    "time_zone": "Asia/Bangkok",
    "ui_language": "in",
    "cdid": "a854d5a9-b6cd-4de7-9c43-8310f5bf513c",
}

def decode_b64(data):
    try:
        if data:
            return base64.b64decode(data).decode('utf-8')
    except:
        pass
    return None

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. API HOME (FITUR LAMA: Recommend + Infinite Scroll Random) ---
@app.route('/api/home', methods=['GET'])
def home():
    try:
        results = []
        offset = request.args.get('offset', '0')
        is_first_load = (str(offset) == '0')

        # A. Bagian Recommended (Hanya saat buka aplikasi pertama kali)
        if is_first_load:
            try:
                url_search = f"{API_HOST}/i18n_novel/search/scroll_recommend/v1/"
                p_search = params.copy()
                p_search.update({
                    "from_scene": "0", "iid": "7555696322994947858", "device_id": "7555694633755166216",
                    "channel": "gp", "version_code": "50018", "version_name": "5.0.0",
                    "device_type": "ASUS_Z01QD", "mcc_mnc": "51001", "carrier_region_v2": "510",
                    "cdid": "69a17f9e-cbed-49b2-9523-4d5397905fdc",
                })
                resp_search = requests.get(url_search, headers=head, params=p_search)
                data_search = resp_search.json().get('data', {})
                scroll_words = data_search.get('scroll_words', [])
                search_infos = data_search.get('search_infos', [])

                for u, i in zip(scroll_words, search_infos):
                    series_id = i.get('search_source_book_id')
                    thumbnail = None
                    try:
                        # Request Detail untuk Thumbnail High Quality
                        url_detail = f"{API_HOST}/novel/player/video_detail/v1/"
                        h_detail = head.copy()
                        h_detail.update({"X-Ss-Stub": "238B6268DE1F0B757306031C76B5397E", "Content-Encoding": "gzip", "Content-Type": "application/json; charset=utf-8", "Content-Length": "157"})
                        payload_detail = {"biz_param": {"detail_page_version": 0, "from_video_id": "", "need_all_video_definition": False, "need_mp4_align": False, "source": 4, "use_os_player": False, "video_id_type": 1}, "series_id": series_id}
                        resp_detail = requests.post(url_detail, headers=h_detail, params=p_search, json=payload_detail)
                        if resp_detail.status_code == 200:
                            thumbnail = resp_detail.json().get('data', {}).get('video_data', {}).get('series_cover')
                    except: pass
                    results.append({"title": u, "series_id": series_id, "thumbnail": thumbnail, "type": "recommended"})
            except Exception as e_rec: print(f"Error Recommended: {e_rec}")

        # B. Bagian Infinite Scroll (Mengisi Home dengan keyword acak)
        try:
            query_list = ['terkuat', 'super', 'tersembunyi', 'dewa', 'naga', 'kaisar', 'mewah', 'cinta', 'presiden', 'menantu' , 'kebangkitan','kekuatan','tak terbatas','reinkarnasi' , 'kuno' , 'abadi']
            selected_query = random.choice(query_list) # Pake random biar home variatif
            tiket = str(int(time.time() * 1000))
            
            urlk = f"{API_HOST}/i18n_novel/search/page/v1/"
            p_disc = params.copy()
            p_disc.update({
                "search_source_id": "clks###", "IsFetchDebug": "false", 
                "offset": offset, "cancel_search_category_enhance": "false", 
                "query": selected_query, "limit": '10', "search_id": "", "_rticket": tiket
            })
            
            res_disc = requests.get(urlk, headers=head, params=p_disc).json().get('data', {}).get('search_data', [])
            for v in res_disc:
                books = v.get('books', []) if 'books' in v else [v]
                for g in books:
                    if g.get("book_id"):
                        results.append({
                            "title": g.get("book_name", "Unknown"), 
                            "series_id": g.get("book_id", ""), 
                            "thumbnail": g.get("thumb_url", ""), 
                            "type": "discovery"
                        })
        except Exception as e_disc: print(f"Error Discovery: {e_disc}")

        return jsonify({"status": "success", "data": results})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500


# --- 2. API SEARCH (FITUR: Pencarian & Kategori Discover) ---
@app.route('/api/search', methods=['GET'])
def search():
    # Ambil query dari parameter URL ?q=judul
    query = request.args.get('q')
    if not query:
        return jsonify({"status": "error", "message": "Query required"}), 400
    
    try:
        results = []
        tiket = str(int(time.time() * 1000))
        urlk = f"{API_HOST}/i18n_novel/search/page/v1/"
        
        # Override params dengan query asli user
        p_search = params.copy()
        p_search.update({
            "search_source_id": "clks###",
            "IsFetchDebug": "false",
            "offset": "0",
            "cancel_search_category_enhance": "false",
            "query": query, # INPUT ASLI USER (Bisa Judul atau Kategori)
            "limit": '20', 
            "search_id": "",
            "_rticket": tiket,
        })
        
        resp = requests.get(urlk, headers=head, params=p_search)
        search_data = resp.json().get('data', {}).get('search_data', [])
        
        for v in search_data:
            books = v.get('books', []) if 'books' in v else [v]
            for g in books:
                if g.get("book_id"):
                    results.append({
                        "title": g.get("book_name", "Unknown"),
                        "series_id": g.get("book_id", ""),
                        "thumbnail": g.get("thumb_url", ""),
                        "type": "search_result"
                    })
                    
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 3. API INFO (Detail Drama + Episode) ---
@app.route('/api/info', methods=['GET'])
def info():
    series_id = request.args.get('series_id')
    if not series_id: return jsonify({"error": "series_id required"}), 400
    try:
        urlx = f"{API_HOST}/novel/player/video_detail/v1/"
        h = head.copy()
        h.update({"X-Ss-Stub": "238B6268DE1F0B757306031C76B5397E", "Content-Encoding": "gzip", "Content-Type": "application/json; charset=utf-8", "Content-Length": "157"})
        data = {"biz_param": {"detail_page_version": 0, "from_video_id": "", "need_all_video_definition": False, "need_mp4_align": False, "source": 4, "use_os_player": False, "video_id_type": 1}, "series_id": series_id}
        y = requests.post(urlx, headers=h, params=params, json=data).json()['data']['video_data']
        ep_list = [{"index": vid['vid_index'], "video_id": vid['vid']} for vid in y['video_list']]
        return jsonify({"status": "success", "data": {"title": y.get('series_name', 'Unknown'), "description": y['series_intro'], "thumbnail": y['series_cover'], "episodes": ep_list}})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500


# --- 4. API STREAM (Link Video) ---
@app.route('/api/stream', methods=['GET'])
def stream():
    video_id = request.args.get('video_id')
    if not video_id: return jsonify({"error": "video_id required"}), 400
    try:
        urlc = f"{API_HOST}/novel/player/video_model/v1/"
        h = head.copy()
        h.update({"X-Ss-Stub": "B7FB786F2CAA8B9EFB7C67A524B73AFB", "Content-Encoding": "gzip", "Content-Type": "application/json; charset=utf-8"})
        data = {"biz_param": {"detail_page_version": 0, "device_level": 3, "from_video_id": "", "need_all_video_definition": True, "need_mp4_align": False, "source": 4, "use_os_player": False, "video_id_type": 0, "video_platform": 3}, "video_id": video_id}
        o = requests.post(urlc, headers=h, params=params, json=data).json()['data']['video_model']
        oso = json.loads(o)['video_list']
        # Mengembalikan link asli (akan digunakan oleh proxy download atau player)
        links = {
            "720p": decode_b64(oso.get('video_5', {}).get('main_url')),
            "540p": decode_b64(oso.get('video_4', {}).get('main_url')),
            "480p": decode_b64(oso.get('video_3', {}).get('main_url')),
            "360p": decode_b64(oso.get('video_2', {}).get('main_url')),
            "240p": decode_b64(oso.get('video_1', {}).get('main_url')),
        }
        return jsonify({"status": "success", "data": links})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500


# --- 5. API DOWNLOAD PROXY (FITUR BARU: Download Backend) ---
@app.route('/api/download', methods=['GET'])
def proxy_download():
    """
    Endpoint ini bertugas mengambil file video dari server aslinya 
    dan meneruskannya ke user sebagai file download.
    User -> Server Flask -> Server Video
    """
    video_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    
    if not video_url:
        return "Missing URL", 400

    try:
        # Request ke source video secara streaming
        req = requests.get(video_url, stream=True, timeout=10)
        
        # Generator untuk mengalirkan data chunk-by-chunk agar RAM server tidak penuh
        def generate():
            for chunk in req.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

        # Return sebagai attachment agar browser langsung download
        return Response(stream_with_context(generate()), headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": req.headers.get('Content-Type', 'video/mp4')
        })
    except Exception as e:
        return f"Download Failed: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, port=3000)
