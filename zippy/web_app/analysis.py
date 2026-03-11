

import numpy as np
from ultralytics import YOLO
import cv2


def extract_video_analysis(video_path, model, max_frames=500):
    """
    Comprehensive video analysis with person-bag association and behavioral inference.
    All processing is local - no external APIs used.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Sampling for efficiency
        sample_rate = max(1, total_frames // max_frames) if max_frames else 1
        
        # Data structures for tracking
        bag_trajectory = []  # List of dicts with frame info
        person_detections = []  # List of all person detections
        
        frame_idx = 0
        frame_count = 0
        
        while frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % sample_rate != 0:
                frame_idx += 1
                continue
            
            # Detect all objects (bags and persons)
            results = model(frame, verbose=False, conf=0.4)
            
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    if class_name == 'Bag':
                        bag_trajectory.append({
                            'frame': frame_idx,
                            'x': center_x,
                            'y': center_y,
                            'conf': confidence,
                            'bbox': (x1, y1, x2, y2)
                        })
                    elif class_name == 'Person':
                        person_detections.append({
                            'frame': frame_idx,
                            'x': center_x,
                            'y': center_y,
                            'conf': confidence,
                            'bbox': (x1, y1, x2, y2)
                        })
            
            frame_count += 1
            frame_idx += 1
        
        cap.release()
        
        if not bag_trajectory:
            return None
        
        # Establish person-bag association
        bag_associations = associate_persons_to_bag(bag_trajectory, person_detections)
        
        # Analyze behavioral patterns
        behavior_analysis = analyze_bag_behavior(
            bag_trajectory, 
            person_detections,
            bag_associations,
            fps,
            sample_rate
        )
        
        # Classify bag status
        bag_status = classify_bag_status(behavior_analysis, bag_trajectory, person_detections)
        
        duration = total_frames / fps if fps > 0 else 0
        
        analysis_data = {
            'fps': float(fps),
            'total_frames': int(total_frames),
            'duration': float(duration),
            'video_dimensions': f"{width}x{height}",
            'bag_trajectory': bag_trajectory,
            'person_detections': person_detections,
            'bag_associations': bag_associations,
            'behavior': behavior_analysis,
            'bag_status': bag_status,
            'sample_rate': sample_rate
        }
        
        return analysis_data
    except Exception as e:
        print(f"Error extracting video analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


def associate_persons_to_bag(bag_trajectory, person_detections, proximity_threshold=200):
    """
    Associate persons to the bag using spatial proximity and temporal consistency.
    Returns dict mapping frame -> list of nearby person data
    """
    associations = {}
    
    for bag_point in bag_trajectory:
        frame = bag_point['frame']
        bag_x, bag_y = bag_point['x'], bag_point['y']
        
        # Find all persons detected in this frame
        nearby_persons = []
        for person in person_detections:
            if person['frame'] == frame:
                dist = np.sqrt((person['x'] - bag_x)**2 + (person['y'] - bag_y)**2)
                if dist <= proximity_threshold:
                    nearby_persons.append({
                        'distance': dist,
                        'x': person['x'],
                        'y': person['y'],
                        'bbox': person['bbox']
                    })
        
        if nearby_persons:
            # Sort by distance - closest person is primary
            nearby_persons.sort(key=lambda p: p['distance'])
            associations[frame] = nearby_persons
    
    return associations


def analyze_bag_behavior(bag_trajectory, person_detections, associations, fps, sample_rate):
    """
    Analyze behavioral patterns of the bag and associated persons.
    """
    if not bag_trajectory or len(bag_trajectory) < 2:
        return {}
    
    # Movement analysis
    distances = []
    for i in range(1, len(bag_trajectory)):
        dx = bag_trajectory[i]['x'] - bag_trajectory[i-1]['x']
        dy = bag_trajectory[i]['y'] - bag_trajectory[i-1]['y']
        dist = np.sqrt(dx**2 + dy**2)
        distances.append(dist)
    
    stationary_frames = sum(1 for d in distances if d < 5)
    total_movement = sum(distances)
    avg_speed = np.mean(distances) if distances else 0
    max_speed = max(distances) if distances else 0
    
    # Proximity analysis
    closest_person_distances = []
    proximity_history = []
    
    for bag_point in bag_trajectory:
        frame = bag_point['frame']
        if frame in associations and associations[frame]:
            closest_dist = associations[frame][0]['distance']
            closest_person_distances.append(closest_dist)
            proximity_history.append(('with_person', closest_dist))
        else:
            proximity_history.append(('unattended', None))
    
    # Detect separation/abandonment
    unattended_sequence = 0
    max_separation = 0
    for prox_type, dist in proximity_history:
        if prox_type == 'unattended':
            unattended_sequence += 1
            max_separation = max(max_separation, unattended_sequence)
        else:
            unattended_sequence = 0
    
    # Interaction events
    interaction_events = []
    if closest_person_distances:
        for i in range(1, len(closest_person_distances)):
            delta = abs(closest_person_distances[i] - closest_person_distances[i-1])
            if delta > 30:
                if closest_person_distances[i] < closest_person_distances[i-1]:
                    interaction_events.append('approach')
                else:
                    interaction_events.append('departure')
    
    behavior = {
        'total_movement': float(total_movement),
        'avg_speed': float(avg_speed),
        'max_speed': float(max_speed),
        'stationary_frames': int(stationary_frames),
        'mobile_frames': int(len(distances) - stationary_frames),
        'mobility_ratio': float(stationary_frames / len(distances)) if distances else 0,
        'avg_proximity': float(np.mean(closest_person_distances)) if closest_person_distances else None,
        'min_proximity': float(min(closest_person_distances)) if closest_person_distances else None,
        'max_proximity': float(max(closest_person_distances)) if closest_person_distances else None,
        'frames_with_person': int(len(closest_person_distances)),
        'frames_unattended': int(len(proximity_history) - len(closest_person_distances)),
        'max_separation_frames': int(max_separation),
        'interaction_events': interaction_events,
        'num_approaches': len([e for e in interaction_events if e == 'approach']),
        'num_departures': len([e for e in interaction_events if e == 'departure'])
    }
    
    return behavior


def classify_bag_status(behavior, bag_trajectory, person_detections):
    """
    Classify the bag's status based on behavioral analysis.
    Possible statuses: Owned, Transferred, Abandoned, Stolen, Uncertain
    """
    if not behavior:
        return 'Unknown'
    
    frames_with = behavior.get('frames_with_person', 0)
    frames_without = behavior.get('frames_unattended', 0)
    max_sep = behavior.get('max_separation_frames', 0)
    mobility = behavior.get('mobility_ratio', 0)
    approaches = behavior.get('num_approaches', 0)
    departures = behavior.get('num_departures', 0)
    avg_prox = behavior.get('avg_proximity')
    total_move = behavior.get('total_movement', 0)
    
    total = frames_with + frames_without if (frames_with + frames_without) > 0 else 1
    person_ratio = frames_with / total
    
    # Classification logic
    if person_ratio > 0.8 and mobility < 0.3:
        return 'Owned - Being Carried'
    elif person_ratio > 0.7 and max_sep < total * 0.15:
        return 'Owned - Under Supervision'
    elif person_ratio > 0.5 and approaches > 0 and departures > 0:
        return 'Transferred - Ownership Changed'
    elif frames_without > total * 0.5 and max_sep > total * 0.4:
        if mobility > 0.7:
            return 'Abandoned - High Risk'
        else:
            return 'Abandoned - Left Behind'
    elif person_ratio < 0.3 and mobility > 0.5 and total_move > 1000:
        return 'Stolen - Rapid Movement'
    else:
        return 'Uncertain - Requires Review'


def generate_summary(analysis_data):
    try:
        if not analysis_data:
            return None, "No analysis data provided"
        
        behavior = analysis_data.get('behavior', {})
        bag_status = analysis_data.get('bag_status', 'Unknown')
        duration = analysis_data.get('duration', 0)
        fps = analysis_data.get('fps', 30)
        
        # Extract key metrics
        frames_with = behavior.get('frames_with_person', 0)
        frames_without = behavior.get('frames_unattended', 0)
        total_frames = frames_with + frames_without if (frames_with + frames_without) > 0 else 1
        person_ratio = (frames_with / total_frames * 100) if total_frames > 0 else 0
        
        mobility = behavior.get('mobility_ratio', 0)
        total_movement = behavior.get('total_movement', 0)
        avg_speed = behavior.get('avg_speed', 0)
        max_speed = behavior.get('max_speed', 0)
        
        avg_prox = behavior.get('avg_proximity')
        min_prox = behavior.get('min_proximity')
        max_prox = behavior.get('max_proximity')
        
        num_approaches = behavior.get('num_approaches', 0)
        num_departures = behavior.get('num_departures', 0)
        max_separation = behavior.get('max_separation_frames', 0)
        stationary_frames = behavior.get('stationary_frames', 0)
        mobile_frames = behavior.get('mobile_frames', 0)
        
        # Build descriptive narrative
        summary_parts = []
        
        # ===== HEADER =====
        mins = int(duration // 60)
        secs = int(duration % 60)
        time_str = f"{mins} minute(s) and {secs} second(s)" if mins > 0 else f"{secs} second(s)"
        
        summary_parts.append("=" * 60)
        summary_parts.append("VIDEO ANALYSIS SUMMARY - BAG TRACKING & BEHAVIORAL INFERENCE")
        summary_parts.append("=" * 60)
        summary_parts.append("")
        
        # ===== STATUS CLASSIFICATION =====
        summary_parts.append(f"CLASSIFICATION: {bag_status}")
        summary_parts.append("")
        
        # ===== TEMPORAL OVERVIEW =====
        summary_parts.append("TEMPORAL OVERVIEW:")
        summary_parts.append(f"   • Video Duration: {time_str}")
        summary_parts.append(f"   • Total Frames Analyzed: {total_frames} frames at {fps:.1f} FPS")
        summary_parts.append(f"   • Observation Period: Comprehensive frame-by-frame analysis")
        summary_parts.append("")
        
        # ===== PERSON-BAG ASSOCIATION ANALYSIS =====
        summary_parts.append("PERSON-BAG ASSOCIATION ANALYSIS:")
        
        if person_ratio > 80:
            assoc_desc = (f"   The bag exhibited a STRONG and CONSISTENT association with a person throughout "
                         f"the entire observation period. The bag was detected within proximity of a person "
                         f"in {frames_with} out of {total_frames} frames ({person_ratio:.1f}% of the time). "
                         f"This indicates the bag was being actively carried, worn, or closely supervised.")
        elif person_ratio > 60:
            assoc_desc = (f"   The bag showed a FREQUENT association with a person during most of the video. "
                         f"A person was detected near the bag in {frames_with} frames ({person_ratio:.1f}% of total), "
                         f"while the bag was unattended for {frames_without} frames. This pattern suggests "
                         f"the bag remained under regular supervision with brief periods of being set down.")
        elif person_ratio > 40:
            assoc_desc = (f"   The bag displayed an ALTERNATING pattern between supervised and unattended states. "
                         f"Person proximity was detected in {frames_with} frames ({person_ratio:.1f}%), while "
                         f"the bag was left unattended for {frames_without} frames ({100-person_ratio:.1f}%). "
                         f"This mixed pattern may indicate normal usage where the bag is temporarily placed "
                         f"down and later retrieved.")
        elif person_ratio > 20:
            assoc_desc = (f"   The bag was LARGELY UNATTENDED throughout the observation period. "
                         f"A person was only detected nearby in {frames_with} frames ({person_ratio:.1f}% of the time), "
                         f"leaving the bag unattended for {frames_without} frames ({100-person_ratio:.1f}%). "
                         f"This extended period without supervision may warrant attention.")
        else:
            assoc_desc = (f"   The bag was PREDOMINANTLY UNATTENDED with minimal human interaction. "
                         f"Person proximity was detected in only {frames_with} frames ({person_ratio:.1f}%), "
                         f"while the bag remained unattended for {frames_without} frames. "
                         f"This prolonged absence of supervision represents a potentially abandoned item.")
        
        summary_parts.append(assoc_desc)
        
        # Maximum separation detail
        if max_separation > 0:
            sep_duration = max_separation / fps if fps > 0 else max_separation
            if sep_duration > 30:
                summary_parts.append(f"   ALERT: Longest continuous unattended period was {max_separation} frames "
                                   f"({sep_duration:.1f} seconds), which exceeds typical temporary placement duration.")
            else:
                summary_parts.append(f"   • Longest unattended period: {max_separation} frames ({sep_duration:.1f} seconds)")
        summary_parts.append("")
        
        # ===== MOVEMENT BEHAVIOR ANALYSIS =====
        summary_parts.append("MOVEMENT BEHAVIOR ANALYSIS:")
        
        if mobility > 0.7:
            move_desc = (f"   The bag remained MOSTLY STATIONARY throughout the video. "
                        f"It was stationary in {stationary_frames} frames ({mobility*100:.1f}%) and mobile in "
                        f"{mobile_frames} frames. The total displacement was {total_movement:.1f} pixels, "
                        f"indicating the bag was placed in a fixed location with minimal movement. "
                        f"This is consistent with a bag being left in place, either temporarily or abandoned.")
        elif mobility < 0.3:
            move_desc = (f"   The bag exhibited FREQUENT and ACTIVE movement patterns. "
                        f"Mobile frames ({mobile_frames}) significantly outnumbered stationary frames ({stationary_frames}), "
                        f"representing {(1-mobility)*100:.1f}% mobility. The bag traveled a total distance of "
                        f"{total_movement:.1f} pixels with an average speed of {avg_speed:.2f} px/frame. "
                        f"This high mobility suggests the bag was being actively carried or transported.")
        else:
            move_desc = (f"   The bag showed a MIXED MOVEMENT pattern with alternating stationary and mobile phases. "
                        f"Stationary periods: {stationary_frames} frames ({mobility*100:.1f}%), "
                        f"Mobile periods: {mobile_frames} frames. Total movement: {total_movement:.1f} pixels. "
                        f"This pattern indicates normal usage where the bag is carried, set down, and picked up again.")
        
        summary_parts.append(move_desc)
        summary_parts.append(f"   • Average Movement Speed: {avg_speed:.2f} pixels per frame")
        summary_parts.append(f"   • Maximum Speed Detected: {max_speed:.2f} pixels per frame")
        
        if max_speed > 50:
            summary_parts.append(f"   WARNING: High-speed movement detected, which may indicate rapid displacement or potential theft.")
        summary_parts.append("")
        
        # ===== PROXIMITY ANALYSIS =====
        if avg_prox is not None:
            summary_parts.append("SPATIAL PROXIMITY ANALYSIS:")
            
            if avg_prox < 100:
                prox_desc = (f"   The bag maintained VERY CLOSE proximity to the associated person. "
                           f"Average distance: {avg_prox:.1f} pixels (intimate zone). "
                           f"Minimum: {min_prox:.1f}px, Maximum: {max_prox:.1f}px. "
                           f"This extremely close distance suggests the bag was being carried on the person's body, "
                           f"held in hand, or worn as a backpack/purse throughout the observation.")
            elif avg_prox < 200:
                prox_desc = (f"   The bag remained in CLOSE proximity to the person. "
                           f"Average distance: {avg_prox:.1f} pixels (personal space). "
                           f"Minimum: {min_prox:.1f}px, Maximum: {max_prox:.1f}px. "
                           f"The bag was within immediate reach, indicating active supervision and ownership. "
                           f"This distance is typical for a bag placed on a table while the owner is seated nearby.")
            elif avg_prox < 350:
                prox_desc = (f"   The bag was at MODERATE distance from the person. "
                           f"Average distance: {avg_prox:.1f} pixels. "
                           f"Distance range: {min_prox:.1f}px to {max_prox:.1f}px. "
                           f"While still within the person's awareness zone, this distance suggests the bag "
                           f"was intentionally placed at a distance (e.g., across the room, near a door).")
            else:
                prox_desc = (f"   The bag was at SIGNIFICANT distance from the person. "
                           f"Average distance: {avg_prox:.1f} pixels (far range). "
                           f"Maximum distance reached: {max_prox:.1f}px. "
                           f"This substantial separation may indicate the bag was left in a different area "
                           f"from the person, raising concern for potential abandonment.")
            
            summary_parts.append(prox_desc)
            summary_parts.append("")
        
        # ===== INTERACTION DYNAMICS =====
        if num_approaches > 0 or num_departures > 0:
            summary_parts.append("INTERACTION DYNAMICS:")
            
            total_interactions = num_approaches + num_departures
            
            if total_interactions > 5:
                inter_desc = (f"   MULTIPLE INTERACTIONS detected: {num_approaches} approach events and "
                            f"{num_departures} departure events. This high interaction count ({total_interactions} total) "
                            f"indicates dynamic behavior with repeated person-bag engagement. ")
                
                if num_approaches > num_departures:
                    inter_desc += (f"The prevalence of approach events suggests people repeatedly moved toward "
                                 f"the bag, which could indicate interest from multiple individuals or "
                                 f"a transfer of ownership scenario.")
                elif num_departures > num_approaches:
                    inter_desc += (f"The higher number of departure events indicates the person(s) repeatedly "
                                 f"moved away from the bag, suggesting it may have been intentionally left "
                                 f"behind or there was inconsistent supervision.")
                else:
                    inter_desc += (f"The balanced approach-departure pattern suggests cyclical behavior where "
                                 f"a person repeatedly engaged with and then distanced from the bag, "
                                 f"typical of normal usage in a static location.")
            elif total_interactions > 2:
                inter_desc = (f"   Moderate interaction activity: {num_approaches} approaches, {num_departures} departures. "
                            f"This indicates some person-bag engagement with changes in proximity over time, "
                            f"consistent with normal bag handling and placement activities.")
            else:
                inter_desc = (f"   Limited interaction detected: {num_approaches} approaches, {num_departures} departures. "
                            f"Minimal proximity changes suggest either sustained contact or prolonged separation "
                            f"with little dynamic interaction.")
            
            summary_parts.append(inter_desc)
            summary_parts.append("")
        
        # ===== RISK ASSESSMENT =====
        summary_parts.append("SECURITY RISK ASSESSMENT:")
        
        if "Abandoned" in bag_status and "High Risk" in bag_status:
            risk_desc = (f"   CRITICAL ALERT - HIGH RISK ABANDONED BAG\n"
                        f"   The analysis indicates this bag has been abandoned with concerning characteristics:\n"
                        f"   • Extended unattended duration ({frames_without} frames)\n"
                        f"   • Minimal person association ({person_ratio:.1f}% supervised)\n"
                        f"   • Maximum separation: {max_separation} frames\n"
                        f"   RECOMMENDATION: This bag requires immediate security attention and investigation.")
        elif "Stolen" in bag_status:
            risk_desc = (f"   CRITICAL ALERT - POTENTIAL THEFT DETECTED\n"
                        f"   Behavioral patterns consistent with unauthorized bag movement:\n"
                        f"   • Rapid displacement detected (max speed: {max_speed:.2f} px/frame)\n"
                        f"   • Low person association during movement\n"
                        f"   • Total movement: {total_movement:.1f} pixels\n"
                        f"   RECOMMENDATION: Review footage for theft confirmation and identify individuals.")
        elif "Abandoned" in bag_status:
            risk_desc = (f"   MODERATE RISK - BAG LEFT BEHIND\n"
                        f"   The bag appears to have been left unattended for an extended period:\n"
                        f"   • Unattended frames: {frames_without} ({100-person_ratio:.1f}% of video)\n"
                        f"   • Largely stationary with minimal supervision\n"
                        f"   RECOMMENDATION: Monitor the location and attempt to identify the owner.")
        elif "Transferred" in bag_status:
            risk_desc = (f"   MEDIUM RISK - OWNERSHIP TRANSFER DETECTED\n"
                        f"   The bag showed evidence of changing hands or owners:\n"
                        f"   • Multiple approach/departure patterns ({num_approaches}/{num_departures})\n"
                        f"   • Varied person proximity over time\n"
                        f"   RECOMMENDATION: Verify if transfer was intentional between known parties.")
        elif "Owned" in bag_status:
            risk_desc = (f"   LOW RISK - NORMAL OWNERSHIP BEHAVIOR\n"
                        f"   The bag exhibited characteristics consistent with legitimate ownership:\n"
                        f"   • High person association ({person_ratio:.1f}% supervised)\n"
                        f"   • Appropriate proximity patterns\n"
                        f"   • Normal movement and interaction dynamics\n"
                        f"   ASSESSMENT: No security concerns identified. Bag appears to be properly supervised.")
        else:
            risk_desc = (f"   UNCERTAIN - INSUFFICIENT DATA FOR CLASSIFICATION\n"
                        f"   The behavioral patterns did not match clear classification criteria.\n"
                        f"   This may be due to:\n"
                        f"   • Complex multi-person interactions\n"
                        f"   • Unusual environmental factors\n"
                        f"   • Insufficient video quality or detection confidence\n"
                        f"   RECOMMENDATION: Manual review recommended for proper assessment.")
        
        summary_parts.append(risk_desc)
        summary_parts.append("")
        
        summary = "\n".join(summary_parts)
        return summary, None
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        return None, str(e)
