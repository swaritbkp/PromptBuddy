"""
Tools UI Module for PromptBuddy
Renderers for the various tool tabs.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from PIL import Image
import time
import io
import pyperclip
import utils
import logic  # New logic module
import ui_components # New UI module

def render_tools_page():
    st.title("🛠️ Prompt Tools")
    
    tabs = st.tabs([
        "🧠 Prompt Lab",
        "🎨 Visual Studio",
        "📄 Doc Analyzer",
        "✨ Optimizer",
        "🧭 Prompt Mentor",
        "🧮 Scorer",
        "🔁 Auto-Evolver",
        "🧪 Tester",
        "⚖️ Compare",
        "📚 History",
        "📊 Analytics",
        "📖 Library",
        "⚡ Batch Ops"
    ])

    # 1. Prompt Lab
    with tabs[0]:
        st.header("🧠 Prompt Lab")
        st.markdown("Create, refine, and manage prompts for any modality.")
        
        mode = st.radio("Mode", ["📝 Text", "🖼️ Image", "📄 Document"], horizontal=True)
        
        if mode == "📝 Text":
            # ONBOARDING HINT
            if not st.session_state.get('onboarding_complete', False):
                st.info("👋 **New here?** Describe what you want to achieve below, and I'll generate a professional prompt for you. You can then optimize, test, or save it!")
                if st.button("✔️ Got it!", key="dismiss_onboarding"):
                    st.session_state.onboarding_complete = True
                    st.rerun()
            
            user_intent = st.text_area(
                "What do you want to achieve?",
                placeholder="E.g., 'I want to write a blog post about AI ethics'",
                height=100
            )
            
            if st.button("✨ Generate Prompt", type="primary", use_container_width=True):
                if user_intent:
                    with st.spinner("Creating your prompt..."):
                        generated_prompt = logic.create_prompt(user_intent)
                        
                    st.markdown("### Generated Prompt")
                    st.text_area("", value=generated_prompt, height=200, key="generated_prompt_display")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📋 Copy"):
                            st.success("Copied to clipboard!")
                    with col2:
                        if st.button("💾 Save to History"):
                            # Logic for saving to history
                            entry = {
                                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "prompt": generated_prompt,
                                "model": st.session_state.selected_model,
                                "output": "Generated",
                                "score": 0,
                                "latency": 0,
                                "project_id": st.session_state.get("current_project", {}).get("id", "default")
                            }
                            st.session_state.prompt_history.append(entry)
                            # Sync logic
                            if 'user' in st.session_state and st.session_state.user and not st.session_state.user.get('local'):
                                utils.sync_history_to_firestore(st.session_state.prompt_history, st.session_state.user['uid'])
                            else:
                                utils.export_to_json(st.session_state.prompt_history, "history.json") # Simplified local save
                            
                            st.success("Saved!")
                    with col3:
                        st.session_state.prompt_to_optimize = generated_prompt
                        st.info("Go to Optimizer tab to refine!")
                    
                    # Version Control UI
                    st.divider()
                    st.subheader("📜 Version Control")
                    
                    # Initialize version history for this session if needed
                    if "current_prompt_id" not in st.session_state:
                         st.session_state.current_prompt_id = str(pd.Timestamp.now().timestamp())

                    if st.button("💾 Save Version"):
                        version = utils.create_version(generated_prompt)
                        st.session_state.version_history = utils.add_version_to_history(
                            st.session_state.current_prompt_id, 
                            version, 
                            st.session_state.version_history
                        )
                        st.success("Version saved!")
                    
                    versions = utils.get_versions(st.session_state.current_prompt_id, st.session_state.version_history)
                    if versions:
                        with st.expander(f"View History ({len(versions)} versions)"):
                            for v in reversed(versions):
                                st.text(f"{v['timestamp']} - Score: {v['score']}")
                                st.code(v['content'])
                                if st.button(f"Restore {v['timestamp']}", key=v['id']):
                                    # In a real app, this would update the input field. 
                                    # For now, we just show it.
                                    st.info("Restored to clipboard (simulated)")
                                    pyperclip.copy(v['content'])

                else:
                    st.warning("Please enter what you want to achieve.")
        
        elif mode == "🖼️ Image":
            st.info("👉 Go to the **Visual Studio** tab for advanced image prompting.")
            
        elif mode == "📄 Document":
            st.info("👉 Go to the **Doc Analyzer** tab for document processing.")

    # 2. Visual Studio
    with tabs[1]:
        st.header("🎨 Visual Studio")
        st.markdown("Analyze images or generate visual content.")
        
        vs_tab1, vs_tab2 = st.tabs(["👀 Analyze Image", "🎨 Generate Image"])
        
        with vs_tab1:
            uploaded_img = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
            if uploaded_img:
                image = Image.open(uploaded_img)
                st.image(image, caption="Uploaded Image", use_container_width=True)
                
                # Auto-upload to cloud (Phase 7)
                if 'user' in st.session_state and st.session_state.user and not st.session_state.user.get('local'):
                    with st.spinner("☁️ Saving to cloud..."):
                        url = utils.upload_file(uploaded_img, st.session_state.user['uid'])
                        if url:
                            st.toast("Saved to Asset Library!", icon="☁️")
                
                analysis_prompt = st.text_input("Prompt for Analysis", "Describe this image in detail and suggest 3 prompts to recreate it.")
                
                if st.button("🔍 Analyze Image", type="primary"):
                    with st.spinner("Analyzing image with Gemini Vision..."):
                        analysis = logic.analyze_image(image, analysis_prompt)
                    st.markdown(analysis)
        
        with vs_tab2:
            gen_prompt = st.text_area("Enter prompt to generate image", height=100)
            if st.button("🎨 Generate", type="primary"):
                st.info(logic.generate_image(gen_prompt))

    # 3. Doc Analyzer
    with tabs[2]:
        st.header("📄 Doc Analyzer")
        st.markdown("Upload documents to extract text, summarize, or generate prompts based on content.")
        
        uploaded_doc = st.file_uploader("Upload Document (PDF/TXT)", type=["pdf", "txt"])
        
        if uploaded_doc:
            # Auto-upload to cloud (Phase 7)
            if 'user' in st.session_state and st.session_state.user and not st.session_state.user.get('local'):
                 with st.spinner("☁️ Saving to cloud..."):
                    url = utils.upload_file(uploaded_doc, st.session_state.user['uid'])
                    if url:
                        st.toast("Saved to Asset Library!", icon="☁️")

            if st.button("📑 Process Document", type="primary"):
                with st.spinner("Extracting text..."):
                    doc_text = logic.process_document(uploaded_doc)
                    st.session_state.doc_text = doc_text
                st.success("Text extracted!")
                
                with st.expander("View Extracted Text"):
                    st.text_area("", value=doc_text, height=200)
                
                st.divider()
                st.subheader("✨ Generate from Document")
                task = st.selectbox("Task", ["Summarize", "Extract Key Prompts", "Q&A"])
                
                if st.button("Run Task"):
                    with st.spinner(f"Running {task}..."):
                        if task == "Summarize":
                            prompt = f"Summarize this document:\n\n{doc_text[:10000]}"
                        elif task == "Extract Key Prompts":
                            prompt = f"Identify and list any prompts or instructions found in this document:\n\n{doc_text[:10000]}"
                        else:
                            prompt = f"List 5 key questions answered by this document:\n\n{doc_text[:10000]}"
                        
                        result = logic.call_gemini(prompt, "gemini-1.5-flash")
                        st.markdown(result)

    # 4. Optimizer
    with tabs[3]:
        st.header("✨ Multi-Model Optimizer")
        st.markdown("Optimize your prompt for specific AI models with custom settings.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_prompt = st.text_area("Prompt to Optimize", height=150, key="opt_input", value=st.session_state.get("prompt_to_optimize", ""))
        
        with col2:
            target_model = st.selectbox("Optimize for:", ["Gemini", "Claude", "GPT", "Grok"])
            creativity = st.slider("Creativity", 0, 10, 5)
            specificity = st.slider("Specificity", 0, 10, 7)
            depth = st.slider("Depth", 0, 10, 6)
        
        if st.button("🚀 Optimize", type="primary", use_container_width=True):
            if input_prompt:
                with st.spinner(f"Optimizing for {target_model}..."):
                    optimized = logic.optimize_for_model(input_prompt, target_model, creativity, specificity, depth)
                    score_data = logic.score_prompt(optimized)
                
                st.divider()
                
                col_before, col_after = st.columns(2)
                
                with col_before:
                    st.subheader("Original")
                    st.text_area("", value=input_prompt, height=200, key="before_opt", disabled=True)
                
                with col_after:
                    st.subheader(f"Optimized for {target_model}")
                    st.text_area("", value=optimized, height=200, key="after_opt")
                
                st.divider()
                
                # Quality Meter
                score = score_data.get("total_score", 0)
                st.markdown(f"### Quality Score: **{score}/100**")
                
                if score >= 90:
                    st.balloons()
                    
                st.progress(score / 100)
                
                with st.expander("📊 Score Breakdown"):
                    st.write(f"**Clarity:** {score_data.get('clarity', 0)}/25")
                    st.write(f"**Context:** {score_data.get('context', 0)}/25")
                    st.write(f"**Specificity:** {score_data.get('specificity', 0)}/25")
                    st.write(f"**Structure:** {score_data.get('structure', 0)}/25")
                    st.info(score_data.get('explanation', ''))
            else:
                st.warning("Please enter a prompt to optimize.")

    # 5. Prompt Mentor
    with tabs[4]:
        st.header("🧭 Prompt Mentor")
        st.markdown("Get expert analysis on why your prompt works or fails, with actionable recommendations.")
        
        mentor_prompt = st.text_area("Enter Prompt to Analyze", height=150, key="mentor_input")
        
        if st.button("🔍 Analyze Prompt", type="primary", use_container_width=True):
            if mentor_prompt:
                with st.spinner("Analyzing your prompt..."):
                    analysis = logic.explain_prompt_quality(mentor_prompt)
                
                st.divider()
                st.markdown(analysis)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Copy Analysis"):
                        st.success("Copied!")
                with col2:
                    if st.button("✨ Send to Optimizer"):
                        st.session_state.prompt_to_optimize = mentor_prompt
                        st.info("Open the Optimizer tab to refine this prompt!")
            else:
                st.warning("Please enter a prompt to analyze.")

    # 6. Scorer
    with tabs[5]:
        st.header("🧮 Prompt Scorer")
        st.markdown("Get an AI-powered quality assessment with bias and readability analysis.")
        
        prompt_to_score = st.text_area("Enter Prompt to Score", height=200, key="scorer_input")
        
        # Display Prompt Metrics BEFORE scoring
        if prompt_to_score:
            st.divider()
            st.markdown("### 📊 Prompt Metrics")
            metrics = utils.calculate_prompt_metrics(prompt_to_score)
            cost_est = utils.estimate_token_cost(prompt_to_score, st.session_state.selected_model)
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("📝 Words", metrics['word_count'])
            with col_m2:
                st.metric("🔢 Characters", metrics['char_count'])
            with col_m3:
                st.metric("💵 Est. Cost", cost_est['cost_formatted'])
            with col_m4:
                st.metric("🧠 Complexity", f"{metrics['complexity_score']}/100")
            
            st.caption(f"📦 Estimated Tokens: {cost_est['estimated_tokens']} | 🕒 Reading Time: ~{metrics['reading_time_seconds']}s")
        
        if st.button("📊 Analyze", type="primary", use_container_width=True):
            if prompt_to_score:
                with st.spinner("Analyzing prompt quality..."):
                    score_result = logic.enhance_prompt_scoring(prompt_to_score)
                
                total = score_result.get("total_score", 0)
                
                # Display Score with enhanced metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Score", f"{total}/100", delta=None)
                with col2:
                    st.metric("Clarity", f"{score_result.get('clarity', 0)}/20")
                with col3:
                    st.metric("Context", f"{score_result.get('context', 0)}/20")
                
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("Specificity", f"{score_result.get('specificity', 0)}/20")
                with col5:
                    st.metric("Structure", f"{score_result.get('structure', 0)}/20")
                with col6:
                    bias_score = score_result.get('bias_free', 0)
                    st.metric("Bias-Free", f"{bias_score}/10")
                
                # Readability metric
                col7, col8, col9 = st.columns(3)
                with col7:
                    readability_score = score_result.get('readability', 0)
                    st.metric("Readability", f"{readability_score}/10")
                
                st.progress(total / 100)
                
                # Analysis and Bias Notes
                st.info("**Analysis:** " + score_result.get('explanation', ''))
                
                bias_notes = score_result.get('bias_notes', 'None')
                if bias_notes and bias_notes.lower() != 'none detected':
                    st.warning(f"⚠️ **Bias Alert:** {bias_notes}")
                else:
                    st.success("✅ No bias detected")
                
                # Quality feedback with CONTEXTUAL SUGGESTION
                if total >= 90:
                    st.success("🎉 Excellent prompt quality!")
                    st.balloons()
                elif total >= 70:
                    st.success("✅ Good prompt quality!")
                else:
                    st.warning("⚠️ Consider optimizing this prompt.")
                    # CONTEXTUAL INTELLIGENCE: Smart suggestion
                    if st.button("✨ Optimize Now", type="primary", key="optimize_from_scorer"):
                        st.info("👉 Opening Optimizer tab... Copy your prompt and go to the Optimizer tab!")
                        st.session_state.prompt_to_optimize = prompt_to_score
            else:
                st.warning("Please enter a prompt.")

    # 7. Auto-Evolver
    with tabs[6]:
        st.header("🔁 Auto-Evolver")
        st.markdown("Automatically refine your prompt through multiple iterations until it reaches target quality.")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            evolver_prompt = st.text_area("Prompt to Evolve", height=150, key="evolver_input")
        
        with col_right:
            target_score = st.slider("Target Score", min_value=70, max_value=100, value=90, step=5)
            max_iterations = st.slider("Max Iterations", min_value=1, max_value=10, value=5)
        
        if st.button("🚀 Start Evolution", type="primary", use_container_width=True):
            if evolver_prompt:
                with st.spinner(f"Evolving prompt... (max {max_iterations} iterations)"):
                    iterations = logic.auto_optimize_until_threshold(evolver_prompt, target_score, max_iterations)
                
                st.divider()
                
                # Evolution Summary
                final_iteration = iterations[-1]
                final_score = final_iteration["score"]
                num_iterations = len(iterations)
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("Final Score", f"{final_score}/100")
                with col_stat2:
                    st.metric("Iterations Used", num_iterations)
                with col_stat3:
                    improvement = final_score - iterations[0]["score"]
                    st.metric("Improvement", f"+{improvement}", delta=improvement)
                
                # Evolution Tree Visualization
                st.subheader("📈 Evolution Progress")
                
                # Create data for tree visualization
                iteration_nums = [it["iteration"] for it in iterations]
                scores = [it["score"] for it in iterations]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=iteration_nums,
                    y=scores,
                    mode='lines+markers',
                    marker=dict(size=12, color=scores, colorscale='Viridis', showscale=True),
                    line=dict(width=3, color='#667eea'),
                    text=[f"Score: {s}" for s in scores],
                    hovertemplate='<b>Iteration %{x}</b><br>Score: %{y}<extra></extra>'
                ))
                
                fig.add_hline(y=target_score, line_dash="dash", line_color="green", 
                             annotation_text=f"Target: {target_score}")
                
                fig.update_layout(
                    title="Score Evolution",
                    xaxis_title="Iteration",
                    yaxis_title="Quality Score",
                    yaxis_range=[0, 100],
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show iteration details
                st.subheader("📝 Evolution History")
                
                for it in iterations:
                    with st.expander(f"Iteration {it['iteration']} - Score: {it['score']}/100"):
                        st.text_area(
                            "Prompt at this iteration:",
                            value=it['prompt'],
                            height=100,
                            key=f"iter_{it['iteration']}_prompt",
                            disabled=True
                        )
                        details = it['details']
                        col_d1, col_d2, col_d3 = st.columns(3)
                        with col_d1:
                            st.write(f"Clarity: {details.get('clarity', 0)}/20")
                            st.write(f"Context: {details.get('context', 0)}/20")
                        with col_d2:
                            st.write(f"Specificity: {details.get('specificity', 0)}/20")
                            st.write(f"Structure: {details.get('structure', 0)}/20")
                        with col_d3:
                            st.write(f"Bias-Free: {details.get('bias_free', 0)}/10")
                            st.write(f"Readability: {details.get('readability', 0)}/10")
                
                # Final Result
                st.divider()
                st.success("✨ **Final Optimized Prompt:**")
                st.text_area("", value=final_iteration["prompt"], height=150, key="final_evolved", disabled=False)
                
                if final_score >= target_score:
                    st.balloons()
                    st.success(f"🎯 Target score of {target_score} achieved!")
                else:
                    st.info(f"ℹ️ Reached {max_iterations} iterations. Final score: {final_score}/{target_score}")
            else:
                st.warning("Please enter a prompt to evolve.")

    # 8. Tester
    with tabs[7]:
        st.header("🧪 Prompt Tester")
        st.markdown("Test your prompt and see the AI response with metrics.")
        
        test_prompt = st.text_area("Prompt to Test", height=150, key="tester_input")
        enable_reflection = st.checkbox("Enable Reflection Mode (AI self-critique)", value=False)
        
        if st.button("▶️ Run Test", type="primary", use_container_width=True):
            if test_prompt:
                start_time = time.time()
                with st.spinner("Running prompt on Gemini..."):
                    response = logic.call_gemini(test_prompt, st.session_state.selected_model)
                latency = round(time.time() - start_time, 2)
                
                st.divider()
                
                st.markdown("### Response")
                st.write(response)
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⏱️ Latency", f"{latency}s")
                with col2:
                    token_estimate = len(response.split())
                    st.metric("📝 Tokens (est.)", token_estimate)
                with col3:
                    st.metric("🤖 Model", st.session_state.selected_model)
                
                # Reflection Mode
                if enable_reflection:
                    st.divider()
                    with st.expander("🧠 AI Reflection", expanded=True):
                        with st.spinner("AI is reflecting on its response..."):
                            reflection = logic.reflect_on_response(test_prompt, response)
                        st.markdown(reflection)
                
                # Actions
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("📋 Copy Response"):
                        st.success("Copied!")
                with col_b:
                    if st.button("💾 Save to History"):
                        entry = {
                            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "prompt": test_prompt,
                            "model": st.session_state.selected_model,
                            "output": response,
                            "score": 0,
                            "latency": latency,
                            "project_id": st.session_state.get("current_project", {}).get("id", "default")
                        }
                        st.session_state.prompt_history.append(entry)
                        # Sync logic
                        if 'user' in st.session_state and st.session_state.user and not st.session_state.user.get('local'):
                            utils.sync_history_to_firestore(st.session_state.prompt_history, st.session_state.user['uid'])
                        else:
                            utils.export_to_json(st.session_state.prompt_history, "history.json")
                        st.success("Saved!")
            else:
                st.warning("Please enter a prompt to test.")

    # 9. Compare
    with tabs[8]:
        st.header("⚖️ Compare Prompts")
        st.markdown("Test two prompts side-by-side and let AI judge the winner.")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Prompt A")
            prompt_a = st.text_area("", height=150, key="compare_a")
        
        with col_b:
            st.subheader("Prompt B")
            prompt_b = st.text_area("", height=150, key="compare_b")
        
        if st.button("⚔️ Compare", type="primary", use_container_width=True):
            if prompt_a and prompt_b:
                with st.spinner("Running both prompts..."):
                    response_a = logic.call_gemini(prompt_a, st.session_state.selected_model)
                    response_b = logic.call_gemini(prompt_b, st.session_state.selected_model)
                    verdict = logic.compare_prompts(prompt_a, prompt_b)
                
                st.divider()
                
                col_res_a, col_res_b = st.columns(2)
                
                with col_res_a:
                    st.markdown("**Response A**")
                    st.write(response_a)
                
                with col_res_b:
                    st.markdown("**Response B**")
                    st.write(response_b)
                
                st.divider()
                
                st.success(f"### 🏆 Verdict\n{verdict}")
            else:
                st.warning("Please enter both prompts.")

    # 10. History
    with tabs[9]:
        st.header("📚 Prompt History")
        st.markdown("View your prompt history and search for similar prompts using semantic memory.")
        
        # Filter by Project
        current_proj_id = st.session_state.get("current_project", {}).get("id", "default")
        filtered_history = [
            h for h in st.session_state.prompt_history 
            if h.get("project_id", "default") == current_proj_id
        ]
        
        if not filtered_history:
            st.info(f"No history for project: {st.session_state.get('current_project', {}).get('name', 'Default')}")
        else:
            st.caption(f"Showing {len(filtered_history)} items for {st.session_state.get('current_project', {}).get('name', 'Default')}")
        
        # CLOUD SYNC BUTTON
        if 'user' in st.session_state and st.session_state.user and not st.session_state.user.get('local'):
            if st.button("☁️ Sync Now", help="Force sync local history to cloud"):
                success, msg = utils.sync_history_to_firestore(st.session_state.prompt_history, st.session_state.user['uid'])
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
        
        # EXPORT FUNCTIONALITY
        if st.session_state.prompt_history:
            st.subheader("📥 Export History")
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                if st.button("📋 Export as JSON", use_container_width=True):
                    json_data, filename = utils.export_to_json(st.session_state.prompt_history)
                    if json_data:
                        st.download_button(
                            label="📦 Download JSON",
                            data=json_data,
                            file_name=filename,
                            mime="application/json",
                            use_container_width=True
                        )
            
            with col_exp2:
                if st.button("📊 Export as CSV", use_container_width=True):
                    csv_data, filename = utils.export_to_csv(st.session_state.prompt_history)
                    if csv_data:
                        st.download_button(
                            label="📦 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True
                        )
            
            with col_exp3:
                if st.button("📑 Export as Markdown", use_container_width=True):
                    md_data, filename = utils.export_to_markdown(st.session_state.prompt_history)
                    if md_data:
                        st.download_button(
                            label="📦 Download MD",
                            data=md_data,
                            file_name=filename,
                            mime="text/markdown",
                            use_container_width=True
                        )
            
            st.divider()
            
            # IMPORT FUNCTIONALITY
            st.subheader("📤 Import History")
            uploaded_file = st.file_uploader("Upload JSON or CSV", type=["json", "csv"])
            if uploaded_file:
                if st.button("Import Prompts"):
                    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                    content = stringio.read()
                    
                    if uploaded_file.name.endswith(".json"):
                        imported, msg = utils.import_from_json(content)
                    else:
                        imported, msg = utils.import_from_csv(content)
                    
                    if imported:
                        st.session_state.prompt_history.extend(imported)
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            
            st.divider()
        
        if st.session_state.prompt_history:
            # Semantic Search
            st.subheader("🔍 Find Similar Prompts")
            search_query = st.text_input("Enter a prompt to find similar ones", key="history_search")
            
            if st.button("Search", key="search_history_btn"):
                if search_query:
                    similar = logic.find_similar_prompts(search_query, st.session_state.prompt_history, top_k=5)
                    
                    if similar and similar[0]["similarity"] > 0:
                        st.success(f"Found {len(similar)} similar prompts:")
                        for idx, item in enumerate(similar, 1):
                            sim_score = item["similarity"]
                            entry = item["entry"]
                            with st.expander(f"#{idx} - Similarity: {sim_score:.2%} - {entry.get('timestamp', 'N/A')}"):
                                st.write(f"**Prompt:** {entry.get('prompt', 'N/A')}")
                                st.write(f"**Model:** {entry.get('model', 'N/A')}")
                                st.write(f"**Score:** {entry.get('score', 0)}")
                    else:
                        st.info("No similar prompts found.")
            
            st.divider()
            
            # Show full history
            st.subheader("All History")
            df = pd.DataFrame(st.session_state.prompt_history)
            st.dataframe(df, use_container_width=True)
            
        else:
            st.info("No history yet. Start creating prompts!")

    # 11. Analytics
    with tabs[10]:
        st.header("📊 Analytics Dashboard")
        
        if st.session_state.prompt_history and len(st.session_state.prompt_history) > 0:
            df = pd.DataFrame(st.session_state.prompt_history)
            
            # Stats
            trends = utils.calculate_trends(st.session_state.prompt_history)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Quality Score", f"{trends['avg_score']:.1f}/100")
            with col2:
                st.metric("Total Prompts", trends['total_prompts'])
            with col3:
                st.metric("Score Trend", trends['score_trend'].title(), delta="Improving" if trends['score_trend']=="improving" else None)
            with col4:
                st.metric("Most Used Model", trends['most_used_model'])
            
            st.divider()
            
            st.divider()
            
            # Charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                if 'score' in df:
                    fig_bar = px.bar(
                        df,
                        x='timestamp',
                        y='score',
                        title="Quality Score Over Time",
                        labels={'score': 'Score', 'timestamp': 'Time'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_chart2:
                if 'model' in df:
                    model_counts = df['model'].value_counts()
                    fig_pie = px.pie(
                        values=model_counts.values,
                        names=model_counts.index,
                        title="Model Usage Distribution"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            # Advanced Charts
            st.subheader("📈 Advanced Insights")
            if 'score' in df and 'prompt' in df:
                df['length'] = df['prompt'].apply(len)
                fig_scatter = px.scatter(
                    df, 
                    x='length', 
                    y='score',
                    color='model' if 'model' in df else None,
                    title="Prompt Length vs Quality Score",
                    labels={'length': 'Character Count', 'score': 'Quality Score'},
                    hover_data=['prompt']
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data yet. Start using the app to see analytics!")

    # 12. Library
    with tabs[11]:
        st.header("📖 Prompt Library")
        st.markdown("Browse and use pre-made templates for common tasks.")
        
        lib_tab1, lib_tab2 = st.tabs(["📚 Templates", "📂 My Assets"])
        
        with lib_tab1:
            if st.session_state.templates:
                # Search
                search_query = st.text_input("🔍 Search Templates", placeholder="e.g., coding, marketing, email...")
                
                if search_query:
                    results = utils.search_templates(st.session_state.templates, search_query)
                else:
                    # Show all flattened
                    results = []
                    for cat, temps in st.session_state.templates.items():
                        for t in temps:
                            t['category'] = cat
                            results.append(t)
                
                # Display
                if results:
                    for t in results:
                        with st.expander(f"{t['name']} ({t.get('category', 'General')})"):
                            st.markdown(f"**Description:** {t.get('description', '')}")
                            st.code(t['prompt'])
                            col_t1, col_t2 = st.columns([1, 4])
                            with col_t1:
                                if st.button("Use Template", key=f"use_{t['name']}"):
                                    st.session_state.prompt_to_optimize = t['prompt']
                                    st.info("Sent to Optimizer!")
                            with col_t2:
                                if st.button("📋 Copy", key=f"copy_{t['name']}"):
                                    pyperclip.copy(t['prompt'])
                                    st.success("Copied!")
                else:
                    st.warning("No templates match your search.")
            else:
                st.error("Templates file not found. Please check templates.json exists.")
        
        with lib_tab2:
            st.subheader("☁️ Cloud Assets")
            if 'user' in st.session_state and st.session_state.user and not st.session_state.user.get('local'):
                files = utils.list_user_files(st.session_state.user['uid'])
                if files:
                    st.caption(f"Found {len(files)} files.")
                    
                    # Grid layout
                    cols = st.columns(3)
                    for i, file in enumerate(files):
                        with cols[i % 3]:
                            with st.container(border=True):
                                if "image" in file['content_type']:
                                    st.image(file['url'], use_container_width=True)
                                else:
                                    st.markdown(f"📄 **{file['name']}**")
                                
                                st.caption(f"Size: {file['size']} bytes")
                                if st.button("📋 Copy URL", key=f"copy_url_{i}"):
                                    pyperclip.copy(file['url'])
                                    st.toast("URL Copied!")
                else:
                    st.info("No assets found. Upload images in Visual Studio or docs in Doc Analyzer.")
            else:
                st.warning("Please sign in to access Cloud Assets.")
            
    with tabs[12]:
        st.header("⚡ Batch Operations")
        st.markdown("Process multiple prompts at once using CSV upload.")
        
        uploaded_batch = st.file_uploader("Upload CSV (must have 'prompt' column)", type=["csv"])
        
        if uploaded_batch:
            df = pd.read_csv(uploaded_batch)
            if 'prompt' in df.columns:
                st.dataframe(df.head(), use_container_width=True)
                st.caption(f"Loaded {len(df)} prompts.")
                
                operation = st.selectbox("Select Operation", ["Score", "Optimize", "Test"])
                
                # Operation Settings
                kwargs = {}
                if operation == "Optimize":
                    kwargs["target_model"] = st.selectbox("Target Model", ["Gemini", "Claude", "GPT", "Grok"], key="batch_opt_model")
                elif operation == "Test":
                    kwargs["model"] = st.session_state.selected_model
                
                if st.button(f"Run Batch {operation}", type="primary"):
                    prompts = df['prompt'].tolist()
                    with st.spinner(f"Processing {len(prompts)} prompts..."):
                        results = logic.process_batch_prompts(prompts, operation, **kwargs)
                    
                    results_df = pd.DataFrame(results)
                    st.success("Batch processing complete!")
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Download
                    csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Results CSV",
                        csv,
                        "batch_results.csv",
                        "text/csv",
                        key='download-csv'
                    )
            else:
                st.error("CSV must contain a 'prompt' column.")
