import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work" / "scripts"))
import daemon_team_console_v2_server as v2  # noqa: E402


class V2ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / ".team" / "daemon_v1").mkdir(parents=True)
        (self.tmp / ".team" / "daemon_v2").mkdir(parents=True)
        registry = {"roles": {
            "SignL3": {"role": "SignL3", "session_id": "s3", "session_id_state": "listed", "live": {"sessionId": "s3", "updatedAt": "2099-01-01T00:00:00Z", "isArchived": False}},
            "signL2": {"role": "signL2", "session_id": "s2", "session_id_state": "listed", "live": {"sessionId": "s2", "updatedAt": "2099-01-01T00:00:00Z", "isArchived": False}},
            "signL8": {"role": "signL8", "session_id": "old", "session_id_state": "stale", "live": {"sessionId": "old", "updatedAt": "2020-01-01T00:00:00Z", "isArchived": False}},
        }}
        (self.tmp / ".team" / "daemon_v1" / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
        (self.tmp / ".team" / "daemon_v1" / "dashboard_data.json").write_text("{}", encoding="utf-8")
        (self.tmp / ".team" / "daemon_migration_4194_manifest.json").write_text("{}", encoding="utf-8")
        (self.tmp / ".team" / "daemon_v2" / "groups.json").write_text(json.dumps({"groups": [{"id": "team-wan", "members": ["SignL3", "signL2"]}]}), encoding="utf-8")
        self.state = v2.V2State(self.tmp, http_get=lambda path: {"path": path})

    def test_mentions_and_group_dry_run_audit(self):
        result = self.state.send({"text": "@team-wan 安全测试消息", "dry_run": True})
        self.assertEqual({x["target"] for x in result["targets"]}, {"SignL3", "signL2"})
        self.assertTrue(self.state.audit_path.exists())
        rows = [json.loads(x) for x in self.state.audit_path.read_text().splitlines()]
        self.assertTrue(all(x["state"] == "dry_run" for x in rows))
        self.assertNotIn("安全测试消息", rows[0]["text_sha256"])

    def test_stale_and_unknown_rejected(self):
        result = self.state.send({"text": "@signL8 test", "dry_run": True})
        self.assertEqual(result["targets"][0]["state"], "rejected_stale")
        with self.assertRaises(ValueError):
            self.state.session_member("not-registered")

    def test_non_dry_run_requires_confirmation(self):
        with self.assertRaises(PermissionError):
            self.state.send({"text": "@signL2 test", "dry_run": False})

    def test_sensitive_preview_redacted(self):
        self.assertNotIn("secret", v2.preview("token=secret"))

    def test_current_session_and_content_blocks(self):
        sent = []
        state = v2.V2State(self.tmp, current_session_id="s2", http_post=lambda path, payload: sent.append((path, payload)) or {})
        result = state.send({"text": "当前 session", "dry_run": False, "confirm": True})
        self.assertEqual(result["targets"][0]["target"], "signL2")
        self.assertEqual(sent[0][1]["prompt"][0]["type"], "text")

    def test_live_check_and_action_dry_run(self):
        state = v2.V2State(self.tmp, http_get=lambda path: {"path": path})
        self.assertTrue(state.live_session("s3")["ok"])
        result = state.session_action("s3", "cancel", {})
        self.assertTrue(result["dry_run"])
        self.assertIn("cancel", result["would_call"])

    def test_host_rejects_non_loopback(self):
        with mock.patch.object(sys, "argv", ["server", "--host", "0.0.0.0"]):
            with self.assertRaises(SystemExit):
                v2.main()


class LocalDataSourceTests(unittest.TestCase):
    """本地数据源层（/api/local/*）离线单元测试：只读 .team/daemon_v1 已落盘文件，绝不连接 daemon。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / ".team" / "daemon_v1").mkdir(parents=True)
        (self.tmp / ".team" / "daemon_v2").mkdir(parents=True)
        self.state = v2.V2State(self.tmp, http_get=lambda path: {"path": path})

    def _write_local_fixtures(self):
        v1 = self.tmp / ".team" / "daemon_v1"
        supervisor = {
            "version": 1, "generated_at": "2026-08-14T10:00:00Z",
            "members": [
                {"role": "SignL3", "unread_count": 3, "last_event_at": "2026-08-14T10:00:00Z",
                 "last_ack_at": None, "processing": 0, "blocked": 0, "failed": 0,
                 "helper_alive": True, "helper_age_seconds": 2.0, "cursor_lag": 0, "last_event_id": 10},
                {"role": "signL2", "unread_count": 1, "last_event_at": "2026-08-14T10:00:01Z",
                 "last_ack_at": None, "processing": 1, "blocked": 0, "failed": 0,
                 "helper_alive": True, "helper_age_seconds": 1.5, "cursor_lag": 0, "last_event_id": 5},
            ],
            "escalations": [{"role": "signL6", "reason": "helper_timeout_or_dead",
                             "created_at": 1786679896.6, "send_prompt": False}],
        }
        (v1 / "message_supervisor.json").write_text(json.dumps(supervisor), encoding="utf-8")
        members = v1 / "members"
        (members / "SignL3").mkdir(parents=True)
        (members / "signL2").mkdir(parents=True)
        # SignL3：helper_error 行必须被跳过；写乱序行验证倒序聚合
        lines3 = [
            {"kind": "helper_error", "error": "TimeoutError", "recorded_at": "2026-08-14T09:00:00Z"},
            {"role": "SignL3", "session_id": "s3", "status": "observed", "observed_at": "2026-08-14T09:00:01Z",
             "event": {"type": "git_status_changed", "data": {"branch": "main", "unstaged": 5, "untracked": 9}}},
            {"role": "SignL3", "session_id": "s3", "status": "observed", "observed_at": "2026-08-14T09:00:02Z",
             "event": {"type": "session_update", "data": {"update": {"sessionUpdate": "agent_message_chunk",
                                                                    "content": {"text": "hello", "type": "text"}}}}},
        ]
        (members / "SignL3" / "inbox.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in lines3), encoding="utf-8")
        lines2 = [
            {"role": "signL2", "session_id": "s2", "status": "observed", "observed_at": "2026-08-14T09:00:10Z",
             "event": {"type": "session_update", "data": {"update": {"sessionUpdate": "user_message_chunk",
                                                                    "content": {"text": "ping", "type": "text"}}}}},
            {"role": "signL2", "session_id": "s2", "status": "observed", "observed_at": "2026-08-14T09:00:11Z",
             "event": {"type": "turn_complete", "data": {}}},
        ]
        (members / "signL2" / "inbox.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in lines2), encoding="utf-8")
        (members / "signL2" / "events.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in lines2), encoding="utf-8")
        return v1, members

    def _chat_rows(self, role="signL2"):
        def su(kind, text, extra=None):
            update = {"sessionUpdate": kind, "content": {"text": text, "type": "text"}}
            if extra:
                update.update(extra)
            return {"role": role, "session_id": "s2", "status": "observed",
                    "observed_at": "2026-08-14T10:00:00Z",
                    "event": {"type": "session_update", "data": {"update": update}}}
        return [
            su("user_message_chunk", "你"),
            su("user_message_chunk", "好"),
            su("agent_message_start", "好的"),
            su("agent_message_chunk", "，稍等"),
            su("agent_thought_chunk", "正在思考"),
            su("tool_call", "", {"toolCallId": "tc1", "title": "web_search", "status": "in_progress"}),
            su("tool_call_update", "", {"toolCallId": "tc1", "status": "completed",
                                        "content": [{"type": "text", "text": "结果A"},
                                                    {"type": "text", "text": "结果B"}]}),
            su("agent_message_chunk", "完成"),
            su("agent_message_end", ""),
        ]

    def test_local_status_ok(self):
        v1, _members = self._write_local_fixtures()
        result = self.state.local_status()
        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "local")
        self.assertEqual(len(result["members"]), 2)
        self.assertEqual(result["members"][0]["role"], "SignL3")
        self.assertEqual(result["escalations"][0]["role"], "signL6")
        self.assertTrue(result["members"][1]["helper_alive"])

    def test_local_status_missing_file_ok_false(self):
        result = self.state.local_status()
        self.assertFalse(result["ok"])
        self.assertIn("message_supervisor", result["error"])

    def test_local_status_corrupt_file_ok_false(self):
        (self.tmp / ".team" / "daemon_v1" / "message_supervisor.json").write_text("{not json", encoding="utf-8")
        result = self.state.local_status()
        self.assertFalse(result["ok"])

    def test_local_messages_aggregate_sorted_and_skip_helper_error(self):
        _v1, _members = self._write_local_fixtures()
        result = self.state.local_messages()
        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "local")
        msgs = result["messages"]
        self.assertEqual(len(msgs), 4)  # SignL3 2 条（helper_error 跳过）+ signL2 2 条
        times = [m["observed_at"] for m in msgs]
        self.assertEqual(times, sorted(times, reverse=True))  # 全局按 observed_at 倒序
        self.assertNotIn("TimeoutError", [m["text"] for m in msgs])
        self.assertEqual(msgs[0]["role"], "signL2")  # 最新 09:00:11 在最前
        self.assertEqual(msgs[0]["type"], "turn_complete")

    def test_local_messages_per_member_cap(self):
        _v1 = self.tmp / ".team" / "daemon_v1"
        members = _v1 / "members"
        (members / "signL9").mkdir(parents=True)
        rows = [{"role": "signL9", "session_id": "s9", "status": "observed",
                 "observed_at": f"2026-08-14T09:{m:02d}:00Z",
                 "event": {"type": "replay_complete", "data": {"replayedCount": 0}}} for m in range(25)]
        (members / "signL9" / "inbox.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
        result = self.state.local_messages()
        self.assertTrue(result["ok"])
        own = [m for m in result["messages"] if m["role"] == "signL9"]
        self.assertEqual(len(own), 20)  # 每成员最多 20 条
        self.assertEqual(own[0]["observed_at"], "2026-08-14T09:24:00Z")  # 取最近

    def test_local_messages_missing_dir_ok_false(self):
        result = self.state.local_messages()
        self.assertFalse(result["ok"])

    def test_local_chat_grouping(self):
        _v1, members = self._write_local_fixtures()
        (members / "signL2" / "events.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in self._chat_rows()), encoding="utf-8")
        result = self.state.local_chat("signL2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["role"], "signL2")
        kinds = [m["kind"] for m in result["messages"]]
        self.assertEqual(kinds, ["user", "assistant", "thought", "tool", "assistant"])
        self.assertEqual(result["messages"][0]["text"], "你好")  # chunk 拼接
        self.assertEqual(result["messages"][1]["text"], "好的，稍等")
        self.assertEqual(result["messages"][2]["text"], "正在思考")
        tool = result["messages"][3]
        self.assertEqual(tool["title"], "web_search")
        self.assertEqual(tool["status"], "completed")
        self.assertEqual(tool["text"], "结果A结果B")  # content-block 数组拼接
        self.assertFalse(result["messages"][4]["streaming"])  # agent_message_end 收尾

    def test_local_chat_max_events(self):
        _v1, members = self._write_local_fixtures()
        rows = [{"role": "signL2", "session_id": "s2", "status": "observed",
                 "observed_at": "2026-08-14T10:00:00Z",
                 "event": {"type": "session_update", "data": {"update": {"sessionUpdate": "user_message_chunk",
                                                                        "content": {"text": "a", "type": "text"}}}}}
                for _ in range(300)]
        (members / "signL2" / "events.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
        result = self.state.local_chat("signL2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["events_parsed"], 200)  # 最多最近 200 条事件
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["text"], "a" * 200)

    def test_local_chat_missing_role_and_file(self):
        result = self.state.local_chat("ghost")
        self.assertFalse(result["ok"])
        result = self.state.local_chat("")
        self.assertFalse(result["ok"])
        self.assertIn("role", result["error"])

    def test_local_endpoints_http_offline(self):
        """真实启动 8466 Handler（端口 0 随机），验证本地端点统一 HTTP 200 + {ok:...}，全程无 daemon 访问。"""
        import http.client
        import threading as _threading
        old_state = v2.Handler.state
        try:
            v2.Handler.state = self.state
            server = v2.ThreadingHTTPServer(("127.0.0.1", 0), v2.Handler)
            port = server.server_address[1]
            serve_thread = _threading.Thread(target=server.serve_forever, daemon=True)
            serve_thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                # 文件缺失 → HTTP 200 + ok:false（不抛 404/500）
                conn.request("GET", "/api/local/status")
                resp = conn.getresponse(); body = json.loads(resp.read())
                self.assertEqual(resp.status, 200); self.assertFalse(body["ok"])
                conn.request("GET", "/api/local/messages")
                resp = conn.getresponse(); body = json.loads(resp.read())
                self.assertEqual(resp.status, 200); self.assertFalse(body["ok"])
                conn.request("GET", "/api/local/chat")
                resp = conn.getresponse(); body = json.loads(resp.read())
                self.assertEqual(resp.status, 200); self.assertFalse(body["ok"])
                conn.request("GET", "/api/local/chat?role=ghost")
                resp = conn.getresponse(); body = json.loads(resp.read())
                self.assertEqual(resp.status, 200); self.assertFalse(body["ok"])
                conn.close()
                # 写入 fixture 后 → ok:true
                self._write_local_fixtures()
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                conn.request("GET", "/api/local/status")
                body = json.loads(conn.getresponse().read())
                self.assertTrue(body["ok"]); self.assertEqual(body["source"], "local")
                self.assertEqual(len(body["members"]), 2)
                conn.request("GET", "/api/local/messages")
                body = json.loads(conn.getresponse().read())
                self.assertTrue(body["ok"]); self.assertEqual(len(body["messages"]), 4)
                conn.request("GET", "/api/local/chat?role=signL2")
                body = json.loads(conn.getresponse().read())
                self.assertTrue(body["ok"]); self.assertIsInstance(body["messages"], list)
                conn.close()
            finally:
                server.shutdown()
                server.server_close()
        finally:
            v2.Handler.state = old_state


class HourlyTrackerTests(unittest.TestCase):
    """分时（hourly）用量追踪：高峰判定 / 分时计价 / 增量解析 / response_id 去重 / 截断重扫。"""

    def _event(self, rid: str, model: str, ts: str, inp: int, cached: int, out: int, thoughts: int = 0) -> dict:
        return {
            "uuid": "u-" + rid, "sessionId": "s1", "timestamp": ts, "type": "system",
            "subtype": "ui_telemetry",
            "systemPayload": {"uiEvent": {
                "event.name": "qwen-code.api_response", "event.timestamp": ts,
                "response_id": rid, "model": model, "status_code": 200,
                "input_token_count": inp, "output_token_count": out,
                "cached_content_token_count": cached, "thoughts_token_count": thoughts,
                "total_token_count": inp + out}},
        }

    def _mk(self):
        tmp = Path(tempfile.mkdtemp())
        chats = tmp / "chats"
        chats.mkdir()
        tracker = v2.HourlyTracker(chats, tmp / "state.json", lambda: [("s1", "主管人")])
        return tmp, chats, tracker

    def test_is_peak_hours(self):
        for h in (9, 10, 11, 14, 15, 16, 17):
            self.assertTrue(v2.HourlyTracker._is_peak(h), f"hour {h} should be peak")
        for h in (0, 7, 8, 12, 13, 18, 23):
            self.assertFalse(v2.HourlyTracker._is_peak(h), f"hour {h} should be off-peak")

    def test_bucket_cost_prices(self):
        flash_off, flash_peak = v2.DS_PRICE_USD["deepseek-v4-flash"], v2.DS_PEAK_USD["deepseek-v4-flash"]
        self.assertEqual(flash_peak["input_cache_hit"], flash_off["input_cache_hit"] * 2)
        # 100 万缓存命中输入 off-peak = $0.007
        usd, cny = v2.HourlyTracker._bucket_cost("deepseek-v4-flash",
                                                 {"input": 2_000_000, "cached": 1_000_000, "output": 1_000_000}, False)
        expect = 1e6 / 1e6 * 0.007 + 1e6 / 1e6 * 0.22 + 1e6 / 1e6 * 0.66  # 0.887
        self.assertAlmostEqual(usd, expect, places=4)
        # 高峰 ×2
        usd_peak, _ = v2.HourlyTracker._bucket_cost("deepseek-v4-flash",
                                                    {"input": 2_000_000, "cached": 1_000_000, "output": 1_000_000}, True)
        self.assertAlmostEqual(usd_peak, expect * 2, places=4)
        # GPT 订阅模型不计费
        self.assertEqual(v2.HourlyTracker._bucket_cost("gpt-5.6-luna",
                                                       {"input": 1_000_000, "cached": 0, "output": 1000}, False), (0.0, 0.0))

    def test_incremental_dedup_and_truncation(self):
        import datetime as _dt
        now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)
        ts = now.isoformat().replace("+00:00", "Z")
        _tmp, chats, tracker = self._mk()
        fp = chats / "s1.jsonl"
        fp.write_text("".join(json.dumps(self._event("r1", "deepseek-v4-flash", ts, 1000, 800, 50, thoughts=10)) + "\n"
                             for _ in range(1)), encoding="utf-8")
        r = tracker.report()
        self.assertTrue(r["ok"])
        t0 = r["today"]
        # 输出含思考：50+10
        self.assertEqual(t0["input_tokens"], 1000)
        self.assertEqual(t0["cached_tokens"], 800)
        self.assertEqual(t0["output_tokens"], 60)
        self.assertEqual(t0["requests"], 1)
        # 增量：追加新事件
        with fp.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(self._event("r2", "deepseek-v4-flash", ts, 500, 400, 20)) + "\n")
        r = tracker.report()
        self.assertEqual(r["today"]["input_tokens"], 1500)
        self.assertEqual(r["today"]["requests"], 2)
        # 去重：追加 r1 的重复（同 response_id）
        with fp.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(self._event("r1", "deepseek-v4-flash", ts, 1000, 800, 50, thoughts=10)) + "\n")
        r = tracker.report()
        self.assertEqual(r["today"]["input_tokens"], 1500)
        self.assertEqual(r["today"]["requests"], 2)
        # 截断/重写：只剩一个新事件 → 全量重扫，桶不再含旧数据
        fp.write_text(json.dumps(self._event("r3", "deepseek-v4-flash", ts, 100, 90, 5)) + "\n", encoding="utf-8")
        r = tracker.report()
        self.assertEqual(r["today"]["input_tokens"], 100)
        self.assertEqual(r["today"]["cached_tokens"], 90)
        self.assertEqual(r["today"]["requests"], 1)

    def test_state_persisted(self):
        _tmp, chats, tracker = self._mk()
        ts = "2026-08-19T04:00:00Z"
        (chats / "s1.jsonl").write_text(
            json.dumps(self._event("r1", "deepseek-v4-flash", ts, 100, 80, 5)) + "\n", encoding="utf-8")
        tracker.report()
        self.assertTrue(tracker.state_path.exists())
        state = json.loads(tracker.state_path.read_text(encoding="utf-8"))
        self.assertEqual(len(state.get("files", {})), 1)
        self.assertIn("s1", state.get("per_file_buckets", {}))


class WorkStatesTests(unittest.TestCase):
    """work_states 判定：prefilling / stalled / idle / error。"""

    def _mk(self, status_payload, pending_payload=None):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".team" / "daemon_v1").mkdir(parents=True)
        (tmp / ".team" / "daemon_v2").mkdir(parents=True)
        registry = {"roles": {
            "SignL3": {"role": "SignL3", "session_id": "s3", "session_id_state": "listed",
                       "live": {"sessionId": "s3", "updatedAt": "2099-01-01T00:00:00Z", "isArchived": False}},
        }}
        (tmp / ".team" / "daemon_v1" / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
        (tmp / ".team" / "daemon_v1" / "dashboard_data.json").write_text("{}", encoding="utf-8")
        (tmp / ".team" / "daemon_migration_4194_manifest.json").write_text("{}", encoding="utf-8")
        (tmp / ".team" / "daemon_v2" / "groups.json").write_text(json.dumps({"groups": []}), encoding="utf-8")

        def fake_get(path):
            if path.endswith("/status"):
                return dict(status_payload)
            if path.endswith("/pending-prompts"):
                return pending_payload if pending_payload is not None else {"pendingPrompts": []}
            return {"path": path}
        return v2.V2State(tmp, http_get=fake_get)

    def test_idle(self):
        state = self._mk({"hasActivePrompt": False, "hasTurnError": False, "updatedAt": "2099-01-01T00:00:00Z"})
        m = state.work_states()["members"][0]
        self.assertEqual(m["state"], "idle")

    def test_prefilling(self):
        import time as _time
        state = self._mk(
            {"hasActivePrompt": True, "hasTurnError": False, "updatedAt": "2099-01-01T00:00:00Z"},
            {"pendingPrompts": [{"state": "running", "queuedAt": int(_time.time() * 1000) - 30_000}]},
        )
        m = state.work_states()["members"][0]
        self.assertEqual(m["state"], "prefilling")

    def test_stalled(self):
        import time as _time
        state = self._mk(
            {"hasActivePrompt": True, "hasTurnError": False, "updatedAt": "2099-01-01T00:00:00Z"},
            {"pendingPrompts": [{"state": "running", "queuedAt": int(_time.time() * 1000) - 360_000}]},
        )
        m = state.work_states()["members"][0]
        self.assertEqual(m["state"], "stalled")

    def test_turn_error(self):
        state = self._mk({"hasActivePrompt": True, "hasTurnError": True, "updatedAt": "2099-01-01T00:00:00Z"})
        m = state.work_states()["members"][0]
        self.assertEqual(m["state"], "error")


class GpuLiveTests(unittest.TestCase):
    """gpu_live：SSH 快照解析 + 成员→模型→GPU 关联。"""

    def _mk(self, snapshot_rows=None, context_model="qwen3.8-27b-q4-lite2(openai)"):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".team" / "daemon_v1").mkdir(parents=True)
        (tmp / ".team" / "daemon_v2").mkdir(parents=True)
        registry = {"roles": {
            "SignL3": {"role": "SignL3", "session_id": "s3", "session_id_state": "listed",
                       "live": {"sessionId": "s3", "updatedAt": "2099-01-01T00:00:00Z", "isArchived": False}},
        }}
        (tmp / ".team" / "daemon_v1" / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
        (tmp / ".team" / "daemon_v1" / "dashboard_data.json").write_text("{}", encoding="utf-8")
        (tmp / ".team" / "daemon_migration_4194_manifest.json").write_text("{}", encoding="utf-8")
        (tmp / ".team" / "daemon_v2" / "groups.json").write_text(json.dumps({"groups": []}), encoding="utf-8")

        def fake_get(path):
            if path.endswith("/context"):
                return {"state": {"models": {"currentModelId": context_model}}}
            return {"path": path}
        state = v2.V2State(tmp, http_get=fake_get)
        state._gpu_snapshot_live = lambda: (snapshot_rows if snapshot_rows is not None else
                                            [{"index": 9, "name": "NVIDIA A30", "util": 97, "used_mib": 24045}])
        return state

    def test_gpu_live_maps_member_to_gpu(self):
        state = self._mk()
        r = state.gpu_live()
        self.assertEqual(r["gpus"][0]["index"], 9)
        self.assertEqual(r["gpus"][0]["util"], 97)
        m = r["members"][0]
        self.assertEqual(m["model"], "qwen3.8-27b-q4-lite2")
        self.assertEqual(m["gpus"], [9])
        self.assertEqual(m["gpu_info"][0]["util"], 97)

    def test_gpu_live_cached(self):
        state = self._mk()
        r1 = state.gpu_live()
        state._gpu_snapshot_live = lambda: [{"index": 9, "name": "NVIDIA A30", "util": 1, "used_mib": 1}]
        r2 = state.gpu_live()
        self.assertEqual(r1["gpus"][0]["util"], r2["gpus"][0]["util"])  # 缓存命中，未重新抓取

    def test_gpu_live_snapshot_error(self):
        state = self._mk(snapshot_rows=[{"error": "TimeoutExpired"}])
        r = state.gpu_live()
        self.assertEqual(r["gpus"], [])
        self.assertIsNotNone(r["snapshot_error"])

    def test_gpu_live_non_local_model(self):
        state = self._mk(context_model="deepseek-v4-flash(openai)")
        r = state.gpu_live()
        m = r["members"][0]
        self.assertFalse(m["local_model"])
        self.assertEqual(m["gpus"], [])

    def _mk_with_jarvis(self, context_model="qwen3.8-27b-q4-lite2(openai)"):
        """在 _mk 基础上补一个 Jarvis unassigned 会话（微信 channel 会话），返回 state。"""
        state = self._mk(context_model=context_model)
        reg = json.loads(state.registry_path.read_text(encoding="utf-8"))
        reg["unassigned_sessions"] = [
            {"displayName": "Jarvis", "sessionId": "jv1", "sourceType": "channel", "isArchived": False},
        ]
        state.registry_path.write_text(json.dumps(reg), encoding="utf-8")
        return state

    def test_gpu_live_captures_jarvis_subagent(self):
        """回归测试（2026-08-30）：Jarvis 启动的 subagent 必须纳入「成员用卡」。

        修复前 _fetch_gpu_live 的 Jarvis 分支只调 _member_gpu，漏掉 _active_tasks(jid)，
        导致 Jarvis 的 sub/side task 用卡不显示。
        """
        state = self._mk_with_jarvis()
        # 桩 _active_tasks：Jarvis 会话派生了一个活跃 subagent（本地模型）
        state._active_tasks = lambda sid: (
            [{"agent_id": "a1", "kind": "subagent", "description": "sub", "status": "running",
              "model": "qwen3.8-27b-q4-tp2", "created_at": "2099-01-01T00:00:00Z",
              "last_updated": "2099-01-01T00:00:00Z", "elapsed_seconds": 10, "stale": False}]
            if sid == "jv1" else []
        )
        r = state.gpu_live()
        subs = [m for m in r["members"] if m["role"] == "Jarvissub"]
        self.assertEqual(len(subs), 1, f"Jarvissub 未出现在 members: {r['members']}")
        self.assertEqual(subs[0]["model"], "qwen3.8-27b-q4-tp2")
        self.assertEqual(subs[0]["task_type"], "subagent")
        self.assertEqual(subs[0]["task_status"], "running")
        # Jarvis 主会话条目仍在
        self.assertTrue(any(m["role"] == "Jarvis" for m in r["members"]))

    def test_gpu_live_captures_jarvis_side_task(self):
        """回归测试（2026-08-30）：Jarvis 启动的 side task 必须纳入「成员用卡」。"""
        state = self._mk_with_jarvis()
        # 桩 _active_tasks：Jarvis 会话派生了一个活跃 side task（本地模型）
        state._active_tasks = lambda sid: (
            [{"agent_id": "st1", "kind": "side_task", "description": "side", "status": "running",
              "model": "qwen3.8-27b-q4-tp2", "created_at": "2099-01-01T00:00:00Z",
              "last_updated": "2099-01-01T00:00:00Z", "elapsed_seconds": 10, "stale": False}]
            if sid == "jv1" else []
        )
        r = state.gpu_live()
        sides = [m for m in r["members"] if m["role"] == "Jarvisside"]
        self.assertEqual(len(sides), 1, f"Jarvisside 未出现在 members: {r['members']}")
        self.assertEqual(sides[0]["model"], "qwen3.8-27b-q4-tp2")
        self.assertEqual(sides[0]["task_type"], "side_task")
        self.assertEqual(sides[0]["task_status"], "running")

    def test_active_subagents_reads_meta_file(self):
        """回归测试：_active_subagents 扫描 meta 文件，只返回活跃且用本地模型的 subagent。

        覆盖：running+本地模型→保留；completed→过滤；running+外部模型→过滤。
        """
        state = self._mk()
        tmp = Path(tempfile.mkdtemp())
        sid = "jv1"
        (tmp / "proj" / "subagents" / sid).mkdir(parents=True)
        base = tmp / "proj" / "subagents" / sid
        # 活跃 subagent（本地模型）→ 应保留
        (base / "agent-running.meta.json").write_text(json.dumps({
            "agentId": "a1", "status": "running",
            "persistedCliFlags": {"model": "qwen3.8-27b-q4-tp2"},
            "createdAt": "2099-01-01T00:00:00Z", "lastUpdatedAt": "2099-01-01T00:00:00Z",
        }), encoding="utf-8")
        # 已完成 subagent → 应过滤
        (base / "agent-done.meta.json").write_text(json.dumps({
            "agentId": "a2", "status": "completed",
            "persistedCliFlags": {"model": "qwen3.8-27b-q4-tp2"},
            "createdAt": "2099-01-01T00:00:00Z", "lastUpdatedAt": "2099-01-01T00:00:00Z",
        }), encoding="utf-8")
        # 外部模型 subagent → 应过滤
        (base / "agent-ext.meta.json").write_text(json.dumps({
            "agentId": "a3", "status": "running",
            "persistedCliFlags": {"model": "deepseek-v4-flash(openai)"},
            "createdAt": "2099-01-01T00:00:00Z", "lastUpdatedAt": "2099-01-01T00:00:00Z",
        }), encoding="utf-8")

        def fake_expanduser(p):
            if p == "~/.qwen/projects":
                return str(tmp)
            return os.path.expanduser(p)

        with mock.patch("os.path.expanduser", side_effect=fake_expanduser):
            tasks = state._active_subagents(sid)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["agent_id"], "a1")
        self.assertEqual(tasks[0]["model"], "qwen3.8-27b-q4-tp2")
        self.assertEqual(tasks[0]["kind"], "subagent")


if __name__ == "__main__":
    unittest.main()
