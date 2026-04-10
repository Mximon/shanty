import gradio as gr
import json
import folium
from folium.plugins import BoatMarker


class EngineInterface:
    def __init__(self, config, engine, system_prompt, hotwords_extractor):
        self.config = config
        self.engine = engine
        self.system_prompt = system_prompt
        self.hotwords_extractor = hotwords_extractor

        # 1. Load the Master Schema JSON instead of CSV
        with open(self.config["paths"]["master_schema"], "r") as f:
            self.ship_data = json.load(f)

        self.hotwords = self.hotwords_extractor.extract_hotwords(self.ship_data)

        self.demo = self._build_interface()

    def _generate_map(self, data):
        own_ship = data["own_ship_telemetry"]
        lat = own_ship["position"]["lat"]
        lon = own_ship["position"]["lon"]
        hdg = own_ship["dynamic"]["heading"]
        sog = own_ship["dynamic"]["speed_over_ground_kn"]

        # Create Map centered on ship
        m = folium.Map(location=[lat, lon], zoom_start=12, tiles="OpenStreetMap")

        # Own Ship Marker
        BoatMarker(
            location=[lat, lon],
            heading=hdg,
            color="blue",
            popup=f"Own Ship: {data['header']['vessel_id']} | HDG: {hdg}° | SOG: {sog}kn",
        ).add_to(m)

        for ship in data["traffic_analysis"]["targets"]:
            s_lat = ship["position"]["lat"]
            s_lon = ship["position"]["lon"]
            s_hdg = ship["dynamic"]["heading"]
            s_sog = ship["dynamic"]["speed_over_ground_kn"]
            BoatMarker(
                location=[s_lat, s_lon],
                heading=s_hdg,
                color="green",
                popup=f"Ship: {ship['name']} | HDG: {s_hdg}° | SOG: {s_sog}kn",
            ).add_to(m)

        # Draw Hazards (e.g., Goodwin Sands)
        for hazard in data["environment"]["geographic_hazards"]:
            # Simple offset logic for visualization purposes
            h_lat = hazard["position"]["lat"]
            h_lon = hazard["position"]["lon"]
            folium.Circle(
                location=[h_lat, h_lon],
                radius=500,
                color="red",
                fill=True,
                popup=f"HAZARD: {hazard['label']}",
            ).add_to(m)

        return m._repr_html_()

    def _process_audio_internal(self, audio_path, history, hotwords):
        if audio_path is None:
            return (
                history,
                None,
                None,
                self.ship_data["own_ship_telemetry"],
                self._generate_map(self.ship_data),
                0,
                0,
                0,
            )

        # --- engine ---
        audio_data, sr, user_text, text_reply, times = self.engine.process_radio_cycle(
            audio_path, self.system_prompt, hotwords
        )
        if user_text is None:
            return (
                history,
                None,
                audio_path,
                self.ship_data["own_ship_telemetry"],
                self._generate_map(self.ship_data),
                0,
                0,
                0,
            )

        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": text_reply})

        # Reload JSON in case the engine updated it
        with open(self.config["paths"]["master_schema"], "r") as f:
            updated_data = json.load(f)

        res_audio = (sr, audio_data) if audio_data is not None else None

        # Return updated components
        return (
            history,
            res_audio,
            audio_path,
            updated_data["own_ship_telemetry"],
            self._generate_map(updated_data),
            times[0] or 0,
            times[1] or 0,
            times[2] or 0,
        )

    def _build_interface(self):
        with gr.Blocks(title="Maritime AI Bridge") as demo:
            history_state = gr.State([])
            hotwords_state = gr.State(self.hotwords)

            gr.Markdown("### MASS Radio Operator")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Radio Communications")
                    input_audio = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="VHF Transmission",
                    )
                    run_btn = gr.Button("TRANSMIT", variant="primary")
                    with gr.Row():
                        stt_time = gr.Number(label="STT (s)", precision=2)
                        llm_time = gr.Number(label="LLM (s)", precision=2)
                        tts_time = gr.Number(label="TTS (s)", precision=2)

                    output_audio = gr.Audio(label="Inbound Radio Response")
                    chatbot = gr.Chatbot(label="Communication Log", height=400)

                with gr.Column(scale=1):
                    gr.Markdown("### Situational Map")
                    map_view = gr.HTML(value=self._generate_map(self.ship_data))

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Vessel Vitals")
                            # Displaying Telemetry as JSON for precision
                            vitals_json = gr.JSON(
                                value=self.ship_data["own_ship_telemetry"]
                            )
                        with gr.Column():
                            gr.Markdown("### Active Logic")
                            # Displaying Rules and Intent
                            logic_json = gr.JSON(
                                value=self.ship_data["decision_engine"]
                            )

            # Event handler
            run_btn.click(
                fn=self._process_audio_internal,
                inputs=[input_audio, history_state, hotwords_state],
                outputs=[
                    chatbot,
                    output_audio,
                    input_audio,
                    vitals_json,
                    map_view,
                    stt_time,
                    llm_time,
                    tts_time,
                ],
            )

        return demo

    def launch(self):
        self.demo.launch(
            server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft()
        )
