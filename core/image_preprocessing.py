"""
Image preprocessing utilities for document orientation correction and enhancement
"""

import cv2
import numpy as np
from PIL import Image, ImageOps
from typing import Dict, Any, Tuple, List
import math


class ImagePreprocessor:
    """Advanced image preprocessing for document orientation and quality improvement"""
    
    def __init__(self):
        self.min_confidence = 0.7  # Minimum confidence for orientation detection
    
    def detect_and_correct_orientation(self, image: Image.Image) -> Dict[str, Any]:
        """
        Detect document orientation and correct if needed
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with corrected image and orientation info
        """
        try:
            print(f"🔍 Starting orientation detection...")
            print(f"   📐 Original image size: {image.size[0]}x{image.size[1]}")
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            print(f"   🖼️  Converted to grayscale for analysis")
            
            # Detect orientation using multiple methods
            orientation_info = self._detect_orientation(gray)
            
            print(f"   📊 Orientation detection results:")
            print(f"      - Needs rotation: {orientation_info['needs_rotation']}")
            print(f"      - Rotation angle: {orientation_info.get('rotation_angle', 0)}°")
            print(f"      - Confidence: {orientation_info.get('confidence', 0):.2f}")
            print(f"      - Method: {orientation_info.get('method', 'unknown')}")
            
            # Apply correction if needed
            corrected_image = image
            rotation_applied = 0
            
            if orientation_info['needs_rotation']:
                rotation_angle = orientation_info['rotation_angle']
                print(f"   🔄 Applying rotation correction: {rotation_angle}°")
                corrected_image = self._rotate_image(image, rotation_angle)
                rotation_applied = rotation_angle
                print(f"   ✅ Rotation applied successfully")
                print(f"   📐 Corrected image size: {corrected_image.size[0]}x{corrected_image.size[1]}")
            else:
                print(f"   ✅ No rotation needed - document appears correctly oriented")
            
            return {
                'corrected_image': corrected_image,
                'original_image': image,
                'orientation_info': orientation_info,
                'rotation_applied': rotation_applied,
                'was_corrected': orientation_info['needs_rotation']
            }
            
        except Exception as e:
            print(f"⚠️  Orientation detection failed: {e}")
            return {
                'corrected_image': image,
                'original_image': image,
                'orientation_info': {'needs_rotation': False, 'confidence': 0},
                'rotation_applied': 0,
                'was_corrected': False,
                'error': str(e)
            }
    
    def _detect_orientation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """
        Detect if document needs rotation using multiple methods
        
        Args:
            gray_image: Grayscale image array
            
        Returns:
            Orientation detection results
        """
        try:
            print(f"   🔬 Running multiple orientation detection methods...")
            
            # Method 1: Text line detection
            print(f"   📝 Method 1: Text line analysis...")
            text_orientation = self._detect_text_orientation(gray_image)
            print(f"      Result: {text_orientation['needs_rotation']} (confidence: {text_orientation['confidence']:.2f})")
            
            # Method 2: Edge detection analysis
            print(f"   📏 Method 2: Edge detection analysis...")
            edge_orientation = self._detect_edge_orientation(gray_image)
            print(f"      Result: {edge_orientation['needs_rotation']} (confidence: {edge_orientation['confidence']:.2f})")
            
            # Method 3: Aspect ratio analysis
            print(f"   📐 Method 3: Aspect ratio analysis...")
            aspect_orientation = self._detect_aspect_ratio_orientation(gray_image)
            print(f"      Result: {aspect_orientation['needs_rotation']} (confidence: {aspect_orientation['confidence']:.2f})")
            
            # Method 4: Upside-down detection
            print(f"   🔄 Method 4: Upside-down detection...")
            upside_down_orientation = self._detect_upside_down(gray_image)
            print(f"      Result: {upside_down_orientation['needs_rotation']} (confidence: {upside_down_orientation['confidence']:.2f})")
            
            # Method 5: Multi-angle rotation detection
            print(f"   🔄 Method 5: Multi-angle rotation detection...")
            multi_angle_orientation = self._detect_multi_angle_rotation(gray_image)
            print(f"      Result: {multi_angle_orientation['needs_rotation']} (confidence: {multi_angle_orientation['confidence']:.2f})")
            
            # Method 6: Skew detection
            print(f"   📐 Method 6: Skew detection...")
            skew_orientation = self._detect_skew(gray_image)
            print(f"      Result: {skew_orientation['needs_rotation']} (confidence: {skew_orientation['confidence']:.2f})")
            
            # Method 7: Diagonal rotation detection
            print(f"   🔄 Method 7: Diagonal rotation detection...")
            diagonal_orientation = self._detect_diagonal_rotation(gray_image)
            print(f"      Result: {diagonal_orientation['needs_rotation']} (confidence: {diagonal_orientation['confidence']:.2f})")
            
            # Method 8: Text orientation detection (horizontal vs vertical)
            print(f"   📝 Method 8: Text orientation detection...")
            text_orientation_detection = self._detect_text_orientation(gray_image)
            print(f"      Result: {text_orientation_detection['needs_rotation']} (confidence: {text_orientation_detection['confidence']:.2f})")
            
            # Combine results
            orientations = [text_orientation, edge_orientation, aspect_orientation, upside_down_orientation, multi_angle_orientation, skew_orientation, diagonal_orientation, text_orientation_detection]
            valid_orientations = [o for o in orientations if o['confidence'] > 0.1]  # Further lowered threshold
            
            print(f"   🎯 Valid methods (confidence > 0.1): {len(valid_orientations)}/8")
            
            if not valid_orientations:
                print(f"   ⚠️  No methods reached confidence threshold - assuming correct orientation")
                return {'needs_rotation': False, 'confidence': 0, 'method': 'none'}
            
            # Be more conservative - only rotate if there's strong evidence
            # Check if any method suggests NO rotation needed
            no_rotation_methods = [o for o in valid_orientations if not o['needs_rotation']]
            rotation_methods = [o for o in valid_orientations if o['needs_rotation']]
            
            # Check document orientation - if it's landscape, it likely needs 90° rotation
            height, width = gray_image.shape
            aspect_ratio = width / height
            is_portrait = aspect_ratio < 0.8  # Good portrait orientation
            is_landscape = aspect_ratio > 1.2  # Landscape orientation
            
            if is_portrait:
                print(f"   📐 Document has good portrait aspect ratio ({aspect_ratio:.2f}) - being extra conservative")
            elif is_landscape:
                print(f"   📐 Document has landscape aspect ratio ({aspect_ratio:.2f}) - likely needs 90° rotation")
            
            if no_rotation_methods:
                # If any method suggests no rotation, be conservative
                best_no_rotation = max(no_rotation_methods, key=lambda x: x['confidence'])
                print(f"   🛡️  Conservative approach: Found {len(no_rotation_methods)} method(s) suggesting no rotation")
                print(f"   🏆 Best no-rotation method: {best_no_rotation['method']} (confidence: {best_no_rotation['confidence']:.2f})")
                
                # Special handling for text orientation detection - it's very reliable for 90° rotations
                text_orientation_methods = [o for o in rotation_methods if o['method'] == 'text_orientation']
                if text_orientation_methods:
                    text_method = text_orientation_methods[0]
                    if text_method['needs_rotation'] and text_method['confidence'] > 0.2:  # Lower threshold for text orientation
                        print(f"   🔄 Text orientation method suggests rotation: {text_method['method']} (confidence: {text_method['confidence']:.2f})")
                        print(f"   ⚠️  Overriding with text orientation evidence - applying 90° rotation")
                        best_orientation = text_method
                    else:
                        # Use normal logic for other methods
                        if is_portrait:
                            min_confidence = 0.9  # Very high confidence needed for portrait docs
                        elif is_landscape:
                            min_confidence = 0.6  # Lower threshold for landscape docs
                        else:
                            min_confidence = 0.85  # Default threshold
                            
                        strong_rotation_methods = [o for o in rotation_methods if o['confidence'] > min_confidence]
                        if strong_rotation_methods:
                            best_rotation = max(strong_rotation_methods, key=lambda x: x['confidence'])
                            print(f"   ⚠️  Overriding with strong rotation evidence: {best_rotation['method']} (confidence: {best_rotation['confidence']:.2f})")
                            best_orientation = best_rotation
                        else:
                            print(f"   ✅ No strong rotation evidence - keeping original orientation")
                            best_orientation = best_no_rotation
                else:
                    # No text orientation method, use normal logic
                    if is_portrait:
                        min_confidence = 0.9  # Very high confidence needed for portrait docs
                    elif is_landscape:
                        min_confidence = 0.6  # Lower threshold for landscape docs
                    else:
                        min_confidence = 0.85  # Default threshold
                        
                    strong_rotation_methods = [o for o in rotation_methods if o['confidence'] > min_confidence]
                    if strong_rotation_methods:
                        best_rotation = max(strong_rotation_methods, key=lambda x: x['confidence'])
                        print(f"   ⚠️  Overriding with strong rotation evidence: {best_rotation['method']} (confidence: {best_rotation['confidence']:.2f})")
                        best_orientation = best_rotation
                    else:
                        print(f"   ✅ No strong rotation evidence - keeping original orientation")
                        best_orientation = best_no_rotation
            else:
                # All methods suggest rotation - use the one with highest confidence
                best_orientation = max(rotation_methods, key=lambda x: x['confidence'])
                print(f"   🏆 All methods suggest rotation - using: {best_orientation['method']} (confidence: {best_orientation['confidence']:.2f})")
            
            return {
                'needs_rotation': best_orientation['needs_rotation'],
                'rotation_angle': best_orientation['rotation_angle'],
                'confidence': best_orientation['confidence'],
                'method': best_orientation['method'],
                'all_methods': orientations
            }
            
        except Exception as e:
            print(f"⚠️  Orientation detection error: {e}")
            return {'needs_rotation': False, 'confidence': 0, 'method': 'error'}
    
    def _detect_text_orientation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect orientation based on text line analysis"""
        try:
            # Apply morphological operations to detect text lines
            kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            # Detect horizontal lines
            horizontal_lines = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN, kernel_horizontal)
            horizontal_count = cv2.countNonZero(horizontal_lines)
            
            # Detect vertical lines
            vertical_lines = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN, kernel_vertical)
            vertical_count = cv2.countNonZero(vertical_lines)
            
            # Calculate confidence based on line density
            total_pixels = gray_image.shape[0] * gray_image.shape[1]
            horizontal_ratio = horizontal_count / total_pixels
            vertical_ratio = vertical_count / total_pixels
            
            print(f"         Horizontal lines: {horizontal_count} ({horizontal_ratio:.4f})")
            print(f"         Vertical lines: {vertical_count} ({vertical_ratio:.4f})")
            
            # Determine if rotation is needed
            if horizontal_ratio > vertical_ratio * 2:
                # Document appears to be in correct orientation
                print(f"         → Correct orientation (horizontal dominant)")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': min(horizontal_ratio * 10, 1.0),
                    'method': 'text_lines'
                }
            elif vertical_ratio > horizontal_ratio * 2:
                # Document appears to be rotated 90 degrees
                print(f"         → Needs rotation (vertical dominant)")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -90,
                    'confidence': min(vertical_ratio * 10, 1.0),
                    'method': 'text_lines'
                }
            else:
                # Ambiguous - try other methods
                print(f"         → Ambiguous (similar horizontal/vertical)")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': 0.3,
                    'method': 'text_lines'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'text_lines', 'error': str(e)}
    
    def _detect_edge_orientation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect orientation based on edge analysis"""
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is None or len(lines) == 0:
                print(f"         No lines detected")
                return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'edges'}
            
            print(f"         Detected {len(lines)} lines")
            
            # Analyze line angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                # Normalize angle to 0-180 range
                if angle > 90:
                    angle -= 180
                angles.append(abs(angle))
            
            # Calculate dominant angle
            angle_counts = {}
            for angle in angles:
                rounded_angle = round(angle)
                angle_counts[rounded_angle] = angle_counts.get(rounded_angle, 0) + 1
            
            if not angle_counts:
                print(f"         No valid angles found")
                return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'edges'}
            
            dominant_angle = max(angle_counts, key=angle_counts.get)
            confidence = angle_counts[dominant_angle] / len(angles)
            
            print(f"         Dominant angle: {dominant_angle}° (confidence: {confidence:.2f})")
            
            # Determine if rotation is needed
            if dominant_angle < 15:  # Nearly horizontal
                print(f"         → Correct orientation (nearly horizontal)")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': confidence,
                    'method': 'edges'
                }
            elif dominant_angle > 75:  # Nearly vertical
                print(f"         → Needs rotation (nearly vertical)")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -90,
                    'confidence': confidence,
                    'method': 'edges'
                }
            else:
                print(f"         → Partial rotation needed ({dominant_angle}°)")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -dominant_angle,
                    'confidence': confidence * 0.7,
                    'method': 'edges'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'edges', 'error': str(e)}
    
    def _detect_aspect_ratio_orientation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect orientation based on aspect ratio analysis"""
        try:
            height, width = gray_image.shape
            
            # Calculate aspect ratio
            aspect_ratio = width / height
            
            print(f"         Image dimensions: {width}x{height}")
            print(f"         Aspect ratio: {aspect_ratio:.2f}")
            
            # Most documents are taller than they are wide
            # If width > height, it might be rotated
            if aspect_ratio > 1.2:  # Landscape orientation
                print(f"         → Landscape orientation detected (likely rotated)")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -90,
                    'confidence': min((aspect_ratio - 1) * 0.5, 0.8),
                    'method': 'aspect_ratio'
                }
            elif aspect_ratio < 0.8:  # Very tall
                print(f"         → Very tall orientation (likely correct)")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': min((1 - aspect_ratio) * 0.5, 0.8),
                    'method': 'aspect_ratio'
                }
            else:  # Square-ish or normal portrait
                print(f"         → Normal portrait/square orientation")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': 0.5,
                    'method': 'aspect_ratio'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'aspect_ratio', 'error': str(e)}
    
    def _detect_upside_down(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect if document is upside down using text density analysis"""
        try:
            height, width = gray_image.shape
            
            # Divide image into top and bottom halves
            top_half = gray_image[:height//2, :]
            bottom_half = gray_image[height//2:, :]
            
            # Calculate text density in each half
            # Use threshold to identify text regions
            _, top_binary = cv2.threshold(top_half, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, bottom_binary = cv2.threshold(bottom_half, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Count text pixels (assuming text is darker than background)
            top_text_pixels = cv2.countNonZero(top_binary)
            bottom_text_pixels = cv2.countNonZero(bottom_binary)
            
            # Calculate densities
            top_area = top_half.shape[0] * top_half.shape[1]
            bottom_area = bottom_half.shape[0] * bottom_half.shape[1]
            
            top_density = top_text_pixels / top_area
            bottom_density = bottom_text_pixels / bottom_area
            
            print(f"         Top half density: {top_density:.4f}")
            print(f"         Bottom half density: {bottom_density:.4f}")
            
            # In a normal document, top usually has more text (headers, titles)
            # If bottom has significantly more text, it might be upside down
            density_ratio = bottom_density / (top_density + 0.001)  # Avoid division by zero
            
            print(f"         Density ratio (bottom/top): {density_ratio:.2f}")
            
            if density_ratio > 1.3:  # Bottom has significantly more text (lowered threshold)
                print(f"         → Likely upside down (bottom-heavy text)")
                return {
                    'needs_rotation': True,
                    'rotation_angle': 180,
                    'confidence': min((density_ratio - 1) * 0.3, 0.8),
                    'method': 'upside_down'
                }
            elif density_ratio < 0.7:  # Top has significantly more text
                print(f"         → Likely correct orientation (top-heavy text)")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': min((1 - density_ratio) * 0.3, 0.8),
                    'method': 'upside_down'
                }
            else:  # Similar densities
                print(f"         → Ambiguous text distribution")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': 0.2,
                    'method': 'upside_down'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'upside_down', 'error': str(e)}
    
    def _detect_multi_angle_rotation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect rotation by testing multiple angles and finding the best text readability"""
        try:
            height, width = gray_image.shape
            
            # Test different rotation angles (including smaller increments for better detection)
            angles_to_test = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345]
            best_angle = 0
            best_score = 0
            
            print(f"         Testing rotation angles: {angles_to_test}")
            
            for angle in angles_to_test:
                # Rotate image
                if angle == 0:
                    test_image = gray_image
                else:
                    # Create PIL image, rotate, convert back to numpy
                    pil_image = Image.fromarray(gray_image)
                    rotated = pil_image.rotate(angle, expand=True)
                    test_image = np.array(rotated)
                
                # Calculate text readability score
                score = self._calculate_text_readability_score(test_image)
                print(f"         Angle {angle}°: score {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_angle = angle
            
            print(f"         Best angle: {best_angle}° (score: {best_score:.3f})")
            
            # Determine if rotation is needed
            if best_angle == 0:
                print(f"         → Correct orientation (no rotation needed)")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': best_score,
                    'method': 'multi_angle'
                }
            else:
                print(f"         → Needs rotation to {best_angle}°")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -best_angle,  # Negative because PIL rotates clockwise
                    'confidence': best_score,
                    'method': 'multi_angle'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'multi_angle', 'error': str(e)}
    
    def _calculate_text_readability_score(self, gray_image: np.ndarray) -> float:
        """Calculate a score indicating how readable the text appears"""
        try:
            # Apply adaptive thresholding to get binary image
            binary = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Calculate horizontal line density (good text should have strong horizontal lines)
            kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_horizontal)
            horizontal_count = cv2.countNonZero(horizontal_lines)
            
            # Calculate vertical line density (should be lower for good text)
            kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_vertical)
            vertical_count = cv2.countNonZero(vertical_lines)
            
            # Calculate aspect ratio score (portrait documents should be taller than wide)
            h, w = gray_image.shape
            aspect_ratio = w / h
            
            # For portrait documents, aspect ratio should be less than 1 (w < h)
            if aspect_ratio < 1.0:
                aspect_score = 1.0 - abs(aspect_ratio - 0.7)  # Optimal aspect ratio around 0.7
            else:
                aspect_score = 0.1  # Landscape orientation gets low score
            
            # Calculate text density (should be reasonable, not too sparse or dense)
            total_pixels = h * w
            text_pixels = cv2.countNonZero(binary)
            text_density = text_pixels / total_pixels
            density_score = 1.0 - abs(text_density - 0.3)  # Optimal density around 0.3
            
            # Combine scores
            horizontal_score = horizontal_count / total_pixels
            vertical_score = vertical_count / total_pixels
            
            # Good text should have more horizontal than vertical lines
            line_ratio_score = horizontal_score / (vertical_score + 0.001)
            
            # Normalize line ratio score
            if line_ratio_score > 1:
                line_ratio_score = 1.0 / line_ratio_score
            
            # Weighted combination of all scores - prioritize aspect ratio for portrait documents
            final_score = (
                horizontal_score * 0.25 +
                line_ratio_score * 0.25 +
                aspect_score * 0.4 +  # Higher weight for aspect ratio
                density_score * 0.1
            )
            
            return min(final_score, 1.0)
            
        except Exception as e:
            return 0.0
    
    def _detect_skew(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect small angle skew using Hough transform"""
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is None or len(lines) == 0:
                print(f"         No lines detected for skew analysis")
                return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'skew'}
            
            print(f"         Detected {len(lines)} lines for skew analysis")
            
            # Analyze line angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                # Normalize angle to -90 to 90 range
                if angle > 90:
                    angle -= 180
                elif angle < -90:
                    angle += 180
                angles.append(angle)
            
            # Calculate mean angle
            mean_angle = np.mean(angles)
            std_angle = np.std(angles)
            
            print(f"         Mean angle: {mean_angle:.2f}°")
            print(f"         Angle std dev: {std_angle:.2f}°")
            
            # Determine if correction is needed
            if abs(mean_angle) > 2:  # More than 2 degrees off
                print(f"         → Skew detected: {mean_angle:.2f}°")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -mean_angle,
                    'confidence': min(abs(mean_angle) / 10, 0.8),
                    'method': 'skew'
                }
            else:
                print(f"         → No significant skew detected")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': 0.5,
                    'method': 'skew'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'skew', 'error': str(e)}
    
    def _detect_diagonal_rotation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect diagonal rotations (like 45 degrees) by analyzing text line orientations"""
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform with more sensitive parameters
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
            
            if lines is None or len(lines) == 0:
                print(f"         No lines detected for diagonal analysis")
                return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'diagonal'}
            
            print(f"         Detected {len(lines)} lines for diagonal analysis")
            
            # Analyze line angles more precisely
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                angles.append(angle)
            
            # Calculate histogram of angles to find dominant orientations
            angle_histogram = {}
            for angle in angles:
                # Round to nearest 5 degrees for grouping
                rounded_angle = round(angle / 5) * 5
                angle_histogram[rounded_angle] = angle_histogram.get(rounded_angle, 0) + 1
            
            print(f"         Angle histogram: {dict(list(angle_histogram.items())[:5])}")  # Show top 5
            
            # Find the most common angle
            if angle_histogram:
                dominant_angle = max(angle_histogram, key=angle_histogram.get)
                dominant_count = angle_histogram[dominant_angle]
                total_lines = len(angles)
                dominance_ratio = dominant_count / total_lines
                
                print(f"         Dominant angle: {dominant_angle}° ({dominant_count}/{total_lines} lines)")
                
                # Check if the dominant angle suggests diagonal rotation
                # For properly oriented text, lines should be close to 0° or 90°
                angle_deviation = min(abs(dominant_angle), abs(dominant_angle - 90), 
                                    abs(dominant_angle - 180), abs(dominant_angle - 270))
                
                print(f"         Angle deviation from cardinal directions: {angle_deviation}°")
                
                if angle_deviation > 10 and dominance_ratio > 0.3:  # Significant diagonal orientation
                    # Calculate correction angle
                    if dominant_angle < 45:
                        correction_angle = -dominant_angle
                    elif dominant_angle < 135:
                        correction_angle = 90 - dominant_angle
                    elif dominant_angle < 225:
                        correction_angle = 180 - dominant_angle
                    elif dominant_angle < 315:
                        correction_angle = 270 - dominant_angle
                    else:
                        correction_angle = 360 - dominant_angle
                    
                    print(f"         → Diagonal rotation detected: {dominant_angle}°")
                    print(f"         → Correction needed: {correction_angle}°")
                    
                    return {
                        'needs_rotation': True,
                        'rotation_angle': correction_angle,
                        'confidence': min(dominance_ratio * 2, 0.9),
                        'method': 'diagonal'
                    }
                else:
                    print(f"         → No significant diagonal rotation detected")
                    return {
                        'needs_rotation': False,
                        'rotation_angle': 0,
                        'confidence': 0.5,
                        'method': 'diagonal'
                    }
            else:
                print(f"         → No angle histogram available")
                return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'diagonal'}
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'diagonal', 'error': str(e)}
    
    
    def _detect_text_orientation(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect if text is oriented horizontally (needs 90° rotation) or vertically (correct)"""
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is None or len(lines) == 0:
                return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'text_orientation'}
            
            # Analyze line angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                angles.append(angle)
            
            # Calculate histogram of angles
            angle_histogram = {}
            for angle in angles:
                rounded_angle = round(angle / 5) * 5
                angle_histogram[rounded_angle] = angle_histogram.get(rounded_angle, 0) + 1
            
            # Count horizontal vs vertical lines
            horizontal_lines = sum(count for angle, count in angle_histogram.items() 
                                 if 0 <= angle <= 15 or 165 <= angle <= 180)
            vertical_lines = sum(count for angle, count in angle_histogram.items() 
                               if 75 <= angle <= 105)
            
            total_lines = len(angles)
            horizontal_ratio = horizontal_lines / total_lines
            vertical_ratio = vertical_lines / total_lines
            
            print(f"         Horizontal lines: {horizontal_lines} ({horizontal_ratio:.2f})")
            print(f"         Vertical lines: {vertical_lines} ({vertical_ratio:.2f})")
            
            # If horizontal lines are significantly more than vertical, needs 90° rotation
            if horizontal_ratio > vertical_ratio * 1.3:  # 30% more horizontal lines
                print(f"         → Horizontal text detected - needs 90° rotation")
                return {
                    'needs_rotation': True,
                    'rotation_angle': -90,  # Rotate 90° counter-clockwise
                    'confidence': min(horizontal_ratio, 0.8),
                    'method': 'text_orientation'
                }
            else:
                print(f"         → Vertical text detected - correct orientation")
                return {
                    'needs_rotation': False,
                    'rotation_angle': 0,
                    'confidence': vertical_ratio,
                    'method': 'text_orientation'
                }
                
        except Exception as e:
            print(f"         → Error: {e}")
            return {'needs_rotation': False, 'rotation_angle': 0, 'confidence': 0, 'method': 'text_orientation', 'error': str(e)}
    
    def _rotate_image(self, image: Image.Image, angle: float) -> Image.Image:
        """
        Rotate image by specified angle
        
        Args:
            image: PIL Image object
            angle: Rotation angle in degrees (positive = clockwise)
            
        Returns:
            Rotated PIL Image
        """
        try:
            # Use PIL's rotate method with proper background
            if image.mode == 'RGBA':
                # For RGBA images, use transparent background
                rotated = image.rotate(angle, expand=True, fillcolor=(255, 255, 255, 0))
            else:
                # For other modes, use white background
                rotated = image.rotate(angle, expand=True, fillcolor=(255, 255, 255))
            
            return rotated
            
        except Exception as e:
            print(f"⚠️  Image rotation failed: {e}")
            return image
    
    def enhance_document_image(self, image: Image.Image) -> Image.Image:
        """
        Apply comprehensive image enhancement for better OCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Enhanced PIL Image
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Apply multiple enhancement techniques
            enhanced = self._apply_contrast_enhancement(img_array)
            enhanced = self._apply_noise_reduction(enhanced)
            enhanced = self._apply_sharpening(enhanced)
            
            # Convert back to PIL
            return Image.fromarray(enhanced)
            
        except Exception as e:
            print(f"⚠️  Image enhancement failed: {e}")
            return image
    
    def _apply_contrast_enhancement(self, img_array: np.ndarray) -> np.ndarray:
        """Apply contrast enhancement using CLAHE"""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels and convert back to RGB
            enhanced_lab = cv2.merge([l, a, b])
            enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
            
            return enhanced_rgb
            
        except Exception as e:
            print(f"⚠️  Contrast enhancement failed: {e}")
            return img_array
    
    def _apply_noise_reduction(self, img_array: np.ndarray) -> np.ndarray:
        """Apply noise reduction using bilateral filter"""
        try:
            # Apply bilateral filter to reduce noise while preserving edges
            denoised = cv2.bilateralFilter(img_array, 9, 75, 75)
            return denoised
            
        except Exception as e:
            print(f"⚠️  Noise reduction failed: {e}")
            return img_array
    
    def _apply_sharpening(self, img_array: np.ndarray) -> np.ndarray:
        """Apply sharpening filter to improve text clarity"""
        try:
            # Create sharpening kernel
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            
            # Apply sharpening
            sharpened = cv2.filter2D(img_array, -1, kernel)
            
            # Ensure values are in valid range
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
            
            return sharpened
            
        except Exception as e:
            print(f"⚠️  Sharpening failed: {e}")
            return img_array
    
    def process_document_page(self, image: Image.Image) -> Dict[str, Any]:
        """
        Complete preprocessing pipeline for a document page
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with processed image and metadata
        """
        try:
            print("🔍 Analyzing document orientation...")
            
            # Step 1: Detect and correct orientation
            orientation_result = self.detect_and_correct_orientation(image)
            corrected_image = orientation_result['corrected_image']
            
            # Step 2: Apply image enhancement
            print("✨ Enhancing image quality...")
            enhanced_image = self.enhance_document_image(corrected_image)
            
            print(f"✅ Document preprocessing completed successfully!")
            if orientation_result['was_corrected']:
                print(f"   🔄 Orientation corrected: {orientation_result['rotation_applied']}°")
            else:
                print(f"   ✅ No orientation correction needed")
            
            return {
                'processed_image': enhanced_image,
                'original_image': image,
                'orientation_corrected': orientation_result['was_corrected'],
                'rotation_applied': orientation_result['rotation_applied'],
                'orientation_info': orientation_result['orientation_info'],
                'enhancement_applied': True,
                'processing_successful': True
            }
            
        except Exception as e:
            print(f"⚠️  Document preprocessing failed: {e}")
            return {
                'processed_image': image,
                'original_image': image,
                'orientation_corrected': False,
                'rotation_applied': 0,
                'orientation_info': {'needs_rotation': False, 'confidence': 0},
                'enhancement_applied': False,
                'processing_successful': False,
                'error': str(e)
            }
