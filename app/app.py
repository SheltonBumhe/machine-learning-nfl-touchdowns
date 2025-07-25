# app/app.py

import streamlit as st
import joblib
import numpy as np
import pandas as pd
import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import NFLDatabase

# Page configuration
st.set_page_config(
    page_title="🏈 NFL QB Touchdown Predictor",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    return NFLDatabase()

db = get_database()

# Load trained model
@st.cache_resource
def load_model():
    try:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'qb_td_model.pkl')
        return joblib.load(model_path)
    except FileNotFoundError:
        st.error("Model file not found. Please train the model first.")
        return None

model = load_model()

def get_qb_list():
    """Get list of QBs from database."""
    try:
        db.connect()
        qbs = pd.read_sql_query("""
            SELECT DISTINCT bs.player_id, bs.name, bs.team
            FROM basic_stats bs
            JOIN game_logs gl ON bs.player_id = gl.player_id
            WHERE bs.position = 'QB' AND gl.position = 'QB'
            ORDER BY bs.name
        """, db.conn)
        db.disconnect()
        return qbs
    except Exception as e:
        st.error(f"Error loading QB list: {e}")
        return pd.DataFrame()

def get_qb_recent_stats(player_id, num_games=3):
    """Get recent stats for a QB."""
    try:
        db.connect()
        stats = pd.read_sql_query("""
            SELECT 
                gl.year, gl.week, gl.team, gl.opponent,
                qs.passing_yards, qs.td_passes, qs.interceptions,
                qs.passes_attempted, qs.passes_completed,
                qs.completion_percentage, qs.yards_per_attempt, qs.passer_rating
            FROM game_logs gl
            JOIN qb_stats qs ON gl.id = qs.game_log_id
            WHERE gl.player_id = ? AND gl.position = 'QB'
            ORDER BY gl.year DESC, gl.week DESC
            LIMIT ?
        """, db.conn, params=(player_id, num_games))
        db.disconnect()
        return stats
    except Exception as e:
        st.error(f"Error loading QB stats: {e}")
        return pd.DataFrame()

def get_qb_basic_info(player_id):
    """Get basic info for a QB."""
    try:
        db.connect()
        info = pd.read_sql_query("""
            SELECT name, age, height, weight, experience, team
            FROM basic_stats
            WHERE player_id = ?
        """, db.conn, params=(player_id,))
        db.disconnect()
        return info.iloc[0] if len(info) > 0 else None
    except Exception as e:
        st.error(f"Error loading QB info: {e}")
        return None

def calculate_features(qb_info, recent_stats):
    """Calculate features for prediction."""
    if recent_stats.empty:
        return None
    
    # Calculate rolling averages
    avg_yards = recent_stats['passing_yards'].mean()
    avg_tds = recent_stats['td_passes'].mean()
    avg_attempts = recent_stats['passes_attempted'].mean()
    avg_completion = recent_stats['completion_percentage'].mean()
    avg_rating = recent_stats['passer_rating'].mean()
    
    # Create feature vector
    features = {
        'age': qb_info['age'],
        'height': qb_info['height'],
        'weight': qb_info['weight'],
        'experience': qb_info['experience'],
        'passing_yards': avg_yards,
        'td_passes': avg_tds,
        'passes_attempted': avg_attempts,
        'completion_percentage': avg_completion,
        'passer_rating': avg_rating
    }
    
    return features

def main():
    st.title("🏈 NFL QB Touchdown Predictor")
    st.markdown("Predict whether a quarterback will throw a touchdown in their next game!")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Make Prediction", "Player Database", "Prediction History", "About"]
    )
    
    if page == "Make Prediction":
        show_prediction_page()
    elif page == "Player Database":
        show_database_page()
    elif page == "Prediction History":
        show_history_page()
    elif page == "About":
        show_about_page()

def show_prediction_page():
    """Show the main prediction page."""
    st.header("🎯 Make a Prediction")
    
    if model is None:
        st.error("Model not available. Please train the model first.")
        return
    
    # Get QB list
    qbs = get_qb_list()
    
    if qbs.empty:
        st.error("No QB data available. Please load data into the database first.")
        return
    
    # Create QB selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Select Quarterback")
        
        # Create a display name for selection
        qbs['display_name'] = qbs['name'] + ' (' + qbs['team'].fillna('Unknown') + ')'
        selected_qb_display = st.selectbox(
            "Choose a quarterback:",
            options=qbs['display_name'].tolist(),
            index=0
        )
        
        # Get selected QB info
        selected_qb_name = selected_qb_display.split(' (')[0]
        selected_qb = qbs[qbs['name'] == selected_qb_name].iloc[0]
        player_id = selected_qb['player_id']
        
        # Get QB basic info
        qb_info = get_qb_basic_info(player_id)
        
        if qb_info is not None:
            st.info(f"**Player Info:** {qb_info['name']}")
            st.info(f"**Age:** {qb_info['age']} | **Experience:** {qb_info['experience']} years")
            st.info(f"**Height:** {qb_info['height']}\" | **Weight:** {qb_info['weight']} lbs")
    
    with col2:
        st.subheader("Game Context")
        
        # Opponent selection
        opponent = st.text_input("Opponent Team (e.g., KC, DEN, NE):", value="")
        
        # Game date
        game_date = st.date_input("Game Date:", value=datetime.now())
        
        # Number of recent games to consider
        num_games = st.slider("Number of recent games to analyze:", 1, 10, 3)
    
    # Get recent stats
    recent_stats = get_qb_recent_stats(player_id, num_games)
    
    if not recent_stats.empty:
        st.subheader("📊 Recent Performance")
        
        # Display recent games
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Recent Games:**")
            for _, game in recent_stats.iterrows():
                st.write(f"**{game['year']} Week {game['week']}** vs {game['opponent']}")
                st.write(f"  {game['passing_yards']} yards, {game['td_passes']} TDs, {game['interceptions']} INTs")
        
        with col2:
            # Calculate averages
            avg_yards = recent_stats['passing_yards'].mean()
            avg_tds = recent_stats['td_passes'].mean()
            avg_attempts = recent_stats['passes_attempted'].mean()
            avg_completion = recent_stats['completion_percentage'].mean()
            
            st.write("**3-Game Averages:**")
            st.write(f"Passing Yards: {avg_yards:.1f}")
            st.write(f"TD Passes: {avg_tds:.1f}")
            st.write(f"Pass Attempts: {avg_attempts:.1f}")
            st.write(f"Completion %: {avg_completion:.1f}%")
        
        # Make prediction
        if st.button("🚀 Predict Touchdown", type="primary"):
            if qb_info is not None:
                # Calculate features
                features = calculate_features(qb_info, recent_stats)
                
                if features:
                    # Create feature vector for model
                    feature_vector = np.array([[
                        features['age'],
                        features['height'],
                        features['weight'],
                        features['experience'],
                        features['passing_yards'],
                        features['td_passes'],
                        features['passes_attempted'],
                        features['completion_percentage'],
                        features['passer_rating']
                    ]])
                    
                    # Make prediction
                    prediction = model.predict(feature_vector)[0]
                    probability = model.predict_proba(feature_vector)[0][1]
                    
                    # Display results
                    st.subheader("🎯 Prediction Results")
                    
                    if prediction == 1:
                        st.success(f"✅ **LIKELY TO THROW A TOUCHDOWN!**")
                        st.success(f"Confidence: {probability:.1%}")
                    else:
                        st.error(f"❌ **UNLIKELY TO THROW A TOUCHDOWN**")
                        st.error(f"Confidence: {1-probability:.1%}")
                    
                    # Save prediction to database
                    if opponent:
                        try:
                            features_json = json.dumps(features)
                            db.save_prediction(
                                player_id=player_id,
                                game_date=game_date.strftime("%Y-%m-%d"),
                                opponent=opponent,
                                prediction=int(prediction),
                                confidence=float(probability if prediction == 1 else 1-probability),
                                features_used=features_json
                            )
                            st.success("Prediction saved to database!")
                        except Exception as e:
                            st.warning(f"Could not save prediction: {e}")
                    
                    # Show feature importance
                    st.subheader("📈 Key Factors")
                    st.write("**Most important features for this prediction:**")
                    
                    # Simple feature importance display
                    feature_importance = {
                        "Recent TD Rate": f"{features['td_passes']:.1f} per game",
                        "Passing Yards": f"{features['passing_yards']:.0f} avg",
                        "Completion %": f"{features['completion_percentage']:.1f}%",
                        "Experience": f"{features['experience']:.0f} years",
                        "Passer Rating": f"{features['passer_rating']:.1f}"
                    }
                    
                    for feature, value in feature_importance.items():
                        st.write(f"• **{feature}:** {value}")
    
    else:
        st.warning("No recent game data available for this quarterback.")

def show_database_page():
    """Show database information page."""
    st.header("🗄️ Player Database")
    
    # Get database summary
    table_info = db.get_table_info()
    
    st.subheader("Database Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Table Records:**")
        for table, count in table_info.items():
            st.write(f"• {table}: {count:,} records")
    
    with col2:
        # Get QB statistics
        try:
            db.connect()
            qb_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(DISTINCT bs.player_id) as total_qbs,
                    COUNT(DISTINCT gl.player_id) as qbs_with_games,
                    COUNT(qs.game_log_id) as total_games,
                    AVG(qs.passing_yards) as avg_yards,
                    AVG(qs.td_passes) as avg_tds
                FROM basic_stats bs
                LEFT JOIN game_logs gl ON bs.player_id = gl.player_id AND gl.position = 'QB'
                LEFT JOIN qb_stats qs ON gl.id = qs.game_log_id
                WHERE bs.position = 'QB'
            """, db.conn)
            db.disconnect()
            
            if not qb_stats.empty:
                stats = qb_stats.iloc[0]
                st.write("**QB Statistics:**")
                st.write(f"• Total QBs: {stats['total_qbs']}")
                st.write(f"• QBs with games: {stats['qbs_with_games']}")
                st.write(f"• Total games: {stats['total_games']:,}")
                st.write(f"• Avg passing yards: {stats['avg_yards']:.1f}")
                st.write(f"• Avg TDs per game: {stats['avg_tds']:.2f}")
        
        except Exception as e:
            st.error(f"Error loading QB stats: {e}")
    
    # Show sample data
    st.subheader("Sample Data")
    
    tab1, tab2, tab3 = st.tabs(["QBs", "Recent Games", "Career Stats"])
    
    with tab1:
        try:
            db.connect()
            sample_qbs = pd.read_sql_query("""
                SELECT name, age, height, weight, experience, team
                FROM basic_stats
                WHERE position = 'QB'
                LIMIT 10
            """, db.conn)
            db.disconnect()
            
            st.dataframe(sample_qbs, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading sample QBs: {e}")
    
    with tab2:
        try:
            db.connect()
            sample_games = pd.read_sql_query("""
                SELECT gl.name, gl.year, gl.week, gl.team, gl.opponent,
                       qs.passing_yards, qs.td_passes, qs.threw_td
                FROM game_logs gl
                JOIN qb_stats qs ON gl.id = qs.game_log_id
                WHERE gl.position = 'QB'
                ORDER BY gl.year DESC, gl.week DESC
                LIMIT 10
            """, db.conn)
            db.disconnect()
            
            st.dataframe(sample_games, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading sample games: {e}")
    
    with tab3:
        try:
            db.connect()
            sample_career = pd.read_sql_query("""
                SELECT cs.name, cs.year, cs.team,
                       qcp.passing_yards, qcp.td_passes, qcp.attempts
                FROM career_stats cs
                JOIN qb_career_passing qcp ON cs.id = qcp.career_id
                WHERE cs.position = 'QB'
                ORDER BY cs.year DESC
                LIMIT 10
            """, db.conn)
            db.disconnect()
            
            st.dataframe(sample_career, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading sample career stats: {e}")

def show_history_page():
    """Show prediction history page."""
    st.header("📊 Prediction History")
    
    # Get prediction history
    try:
        history = db.get_prediction_history()
        
        if not history.empty:
            st.subheader("Recent Predictions")
            
            # Display recent predictions
            for _, pred in history.head(10).iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{pred['name']}** vs {pred['opponent']}")
                    st.write(f"Date: {pred['game_date']}")
                
                with col2:
                    if pred['prediction'] == 1:
                        st.success("✅ TD Predicted")
                    else:
                        st.error("❌ No TD Predicted")
                
                with col3:
                    st.write(f"Confidence: {pred['confidence']:.1%}")
                
                st.divider()
            
            # Show statistics
            st.subheader("Prediction Statistics")
            
            total_predictions = len(history)
            td_predictions = (history['prediction'] == 1).sum()
            avg_confidence = history['confidence'].mean()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Predictions", total_predictions)
            
            with col2:
                st.metric("TD Predictions", td_predictions, f"{td_predictions/total_predictions*100:.1f}%")
            
            with col3:
                st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        else:
            st.info("No predictions have been made yet.")
    
    except Exception as e:
        st.error(f"Error loading prediction history: {e}")

def show_about_page():
    """Show about page."""
    st.header("ℹ️ About This Project")
    
    st.markdown("""
    ## 🏈 NFL QB Touchdown Predictor
    
    This application uses machine learning to predict whether an NFL quarterback will throw a touchdown in their next game.
    
    ### Features:
    - **Database-driven**: All data is stored in a SQLite database for easy management
    - **Real-time predictions**: Make predictions using current player data
    - **Historical tracking**: View prediction history and accuracy
    - **Player database**: Browse all available quarterback data
    
    ### How it works:
    1. **Data Collection**: NFL game logs, career stats, and player information
    2. **Feature Engineering**: Rolling averages, player characteristics, recent performance
    3. **Machine Learning**: XGBoost model trained on historical data
    4. **Prediction**: Real-time predictions with confidence scores
    
    ### Data Sources:
    - Game logs from NFL.com
    - Player career statistics
    - Basic player information (age, height, weight, experience)
    
    ### Model Performance:
    - **Accuracy**: ~88%
    - **F1 Score**: ~85%
    - **ROC-AUC**: ~91%
    
    ---
    
    **Built with ❤️ by Shelton Bumhe**
    
    *Data Scientist | Software Developer | NFL Fan*
    """)

if __name__ == "__main__":
    main()
